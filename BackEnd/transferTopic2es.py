import json
import mysql.connector
from elasticsearch import Elasticsearch, helpers, exceptions as es_exceptions

# MySQL 配置
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'paperbackenddb'
}

# Elasticsearch 配置
es_config = {
    'host': 'http://localhost:9200',
    'username': 'elastic',
    'password': '123456'
}

index_name = 'topics_index_v1'


def parse_json_field(data):
    """解析JSON字段"""
    if not data:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def fetch_topic_data(limit=None, offset=0):
    """从MySQL数据库中获取Topic数据"""
    conn = mysql.connector.connect(**mysql_config)
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM topics_topic ORDER BY topic_id ASC"
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return rows


def get_existing_topic_ids(es, index, topic_ids):
    """批量检查哪些 topic_id 已存在于 Elasticsearch 中"""
    if not topic_ids:
        return set()

    query = {
        "query": {
            "terms": {
                "openalex_topic_id.keyword": list(topic_ids)
            }
        },
        "_source": ["openalex_topic_id"],  # 确保返回 _source 字段
        "size": len(topic_ids)
    }
    response = es.search(index=index, body=query)
    existing_ids = set(hit['_source']['openalex_topic_id']
                       for hit in response['hits']['hits'])
    return existing_ids


def migrate_topic_data(batch_size, max_records, offset=0):
    """
    将Topic数据从MySQL迁移到Elasticsearch
    :param batch_size: 每次迁移的记录数
    :param max_records: 最大迁移记录数，设置为None则迁移所有记录
    :param offset: 数据库查询的偏移量
    """
    es = Elasticsearch(
        hosts=[es_config['host']],
        basic_auth=(es_config['username'], es_config['password']),
        timeout=60
    )

    # 初始化索引（如果尚未创建）
    if not es.indices.exists(index=index_name):
        # 定义索引映射
        index_body = {
            "mappings": {
                "properties": {
                    "topic_id": {"type": "integer"},
                    "openalex_topic_id": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "display_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "works_count": {"type": "integer"},
                    "cited_by_count": {"type": "integer"},
                    "description": {"type": "text"},
                    "keywords": {
                        "type": "keyword"
                    },
                    "siblings": {
                        "type": "nested",
                        "properties": {
                            "id": {
                                "type": "text",
                                "fields": {
                                    "keyword": {"type": "keyword"}
                                }
                            },
                            "display_name": {
                                "type": "text",
                                "fields": {
                                    "keyword": {"type": "keyword"}
                                }
                            }
                        }
                    },
                    "topic_papers": {
                        "type": "nested",
                        "properties": {
                            "paper_id": {"type": "integer"},
                            "title": {
                                "type": "text",
                                "fields": {
                                    "keyword": {"type": "keyword"}
                                }
                            }
                        }
                    }
                }
            }
        }
        es.indices.create(index=index_name, body=index_body)
        print(f"创建 Elasticsearch 索引 {index_name}")

    total_migrated = 0
    total_duplicates = 0
    print(f"总共需要迁移 {max_records} 条 Topic 数据")

    while True:
        rows = fetch_topic_data(limit=batch_size, offset=offset)
        if not rows:
            break
        if max_records is not None and total_migrated >= max_records:
            break
        if max_records is not None:
            remaining = max_records - total_migrated
            if remaining < batch_size:
                rows = rows[:remaining]

        # 批次内去重 based on openalex_topic_id
        unique_rows = {}
        for row in rows:
            openalex_id = row.get('openalex_topic_id')
            if openalex_id and openalex_id not in unique_rows:
                unique_rows[openalex_id] = row
            else:
                total_duplicates += 1  # 批次内重复
        unique_openalex_ids = set(unique_rows.keys())

        # 从 Elasticsearch 批量检查哪些 openalex_topic_id 已存在
        existing_openalex_ids = get_existing_topic_ids(
            es, index_name, unique_openalex_ids)

        actions = []
        batch_duplicates = 0
        for openalex_id, row in unique_rows.items():
            if openalex_id in existing_openalex_ids:
                batch_duplicates += 1
                continue

            doc_id = row['topic_id']
            keywords = parse_json_field(row.get('keywords'))
            siblings = parse_json_field(row.get('siblings'))
            topic_papers = parse_json_field(row.get('topic_papers'))

            doc = {
                "topic_id": doc_id,
                "openalex_topic_id": openalex_id,
                "display_name": row.get('display_name', ""),
                "works_count": row.get('works_count', 0),
                "cited_by_count": row.get('cited_by_count', 0),
                "description": row.get('description', ""),
                "keywords": keywords if keywords else [],
                "siblings": siblings if siblings else [],
                "topic_papers": topic_papers if topic_papers else []
            }

            action = {
                "_index": index_name,
                "_id": doc_id,
                "_source": doc
            }
            actions.append(action)

        try:
            helpers.bulk(es, actions)
            migrated_count = len(actions)
            total_migrated += migrated_count
            total_duplicates += batch_duplicates
            total_processed = total_migrated + total_duplicates
            print(f"成功迁移 {migrated_count} 条 Topic 数据到 {index_name}")
            print(f"本批次重复数据 {batch_duplicates} 条")
            print(f"累计迁移 {total_migrated} 条 Topic 数据，总共需要迁移 {max_records} 条数据")
            print(f"累计处理数据（成功+重复） {total_processed} 条")
        except es_exceptions.BulkIndexError as e:
            print("BulkIndexError:")
            for error in e.errors:
                print(json.dumps(error, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"迁移 Topic 数据时出错: {str(e)}")

        offset += batch_size
        if max_records is not None and total_migrated >= max_records:
            break

    print("脚本运行成功")


if __name__ == "__main__":
    # 在这里传递具体的参数值，包括偏移量
    migrate_topic_data(batch_size=5000, max_records=5000000, offset=0)
