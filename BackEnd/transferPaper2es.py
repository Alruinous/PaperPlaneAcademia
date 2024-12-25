import json
import mysql.connector
from elasticsearch import Elasticsearch, helpers, exceptions as es_exceptions
from datetime import datetime
import time

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

index_name = 'papers_index_v2'


def parse_json_field(data):
    if not data:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def parse_date_field(date_str):
    if not date_str:
        return None
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).isoformat()
        except ValueError:
            continue
    return None


def fetch_data_from_mysql(limit=None, offset=0):
    conn = mysql.connector.connect(**mysql_config)
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM papers_paper ORDER BY paper_id ASC"
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return rows


def get_existing_paper_ids(es, index, paper_ids):
    """批量检查哪些 openalex_paper_id 已存在于 Elasticsearch 中"""
    if not paper_ids:
        return set()

    query = {
        "query": {
            "terms": {
                "openalex_paper_id.keyword": list(paper_ids)
            }
        },
        "_source": ["openalex_paper_id"],  # 确保返回 _source 字段
        "size": 1000  # 每次查询的大小
    }

    existing_ids = set()
    response = es.search(index=index, body=query, scroll='2m')
    scroll_id = response['_scroll_id']
    hits = response['hits']['hits']

    while hits:
        for hit in hits:
            existing_ids.add(hit['_source']['openalex_paper_id'])
        response = es.scroll(scroll_id=scroll_id, scroll='2m')
        scroll_id = response['_scroll_id']
        hits = response['hits']['hits']

    es.clear_scroll(scroll_id=scroll_id)
    return existing_ids


def migrate_data_to_elasticsearch(batch_size, max_records, offset=0):
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
                    "paper_id": {"type": "integer"},
                    "title": {"type": "text"},
                    "institutions": {
                        "type": "nested",
                        "properties": {
                            "display_name": {"type": "text"},
                            "institution_id": {"type": "text"}
                        }
                    },
                    "publish_date": {"type": "date"},
                    "journal": {"type": "text"},
                    "volume": {"type": "text"},
                    "issue": {"type": "text"},
                    "doi": {"type": "text"},
                    "favorites": {"type": "integer"},
                    "abstract": {"type": "text"},
                    "keywords": {"type": "keyword"},
                    "citation_count": {"type": "integer"},
                    "download_link": {"type": "text"},
                    "original_link": {"type": "text"},
                    "references_works": {
                        "type": "nested",
                        "properties": {
                            "reference_id": {"type": "integer"},
                            "title": {"type": "text"}
                        }
                    },
                    "research_fields": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "text"},
                            "display_name": {"type": "text"}
                        }
                    },
                    "status": {"type": "text"},
                    "created_time": {"type": "date"},
                    "openalex_paper_id": {"type": "keyword"},
                    "authorships": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "text"},
                            "display_name": {"type": "text"}
                        }
                    },
                    "related_works": {
                        "type": "nested",
                        "properties": {
                            "related_id": {"type": "integer"},
                            "title": {"type": "text"}
                        }
                    }
                }
            }
        }
        es.indices.create(index=index_name, body=index_body)
        print(f"创建 Elasticsearch 索引 {index_name}")

    total_migrated = 0
    total_duplicates = 0
    print(f"总共需要迁移 {max_records} 条 Paper 数据")

    while True:
        start_time = time.time()
        rows = fetch_data_from_mysql(limit=batch_size, offset=offset)
        fetch_time = time.time()
        print(f"从 MySQL 获取数据用时: {fetch_time - start_time:.2f} 秒")

        if not rows:
            break
        if max_records is not None and total_migrated >= max_records:
            break
        if max_records is not None:
            remaining = max_records - total_migrated
            if remaining < batch_size:
                rows = rows[:remaining]

        # 批次内去重 based on openalex_paper_id
        unique_rows = {}
        for row in rows:
            openalex_id = row.get('openalex_paper_id')
            if openalex_id and openalex_id not in unique_rows:
                unique_rows[openalex_id] = row
            else:
                total_duplicates += 1  # 批次内重复
        unique_openalex_ids = set(unique_rows.keys())

        # 从 Elasticsearch 批量检查哪些 openalex_paper_id 已存在
        existing_openalex_ids = get_existing_paper_ids(
            es, index_name, unique_openalex_ids)
        check_time = time.time()
        print(f"检查 Elasticsearch 中的现有数据用时: {check_time - fetch_time:.2f} 秒")

        actions = []
        batch_duplicates = 0
        for openalex_id, row in unique_rows.items():
            if openalex_id in existing_openalex_ids:
                batch_duplicates += 1
                continue

            doc_id = row['paper_id']
            institutions_val = parse_json_field(row.get('institutions'))
            abstract_val = parse_json_field(row.get('abstract'))
            keywords_val = parse_json_field(row.get('keywords'))
            references_works_val = parse_json_field(
                row.get('references_works'))
            research_fields_val = parse_json_field(row.get('research_fields'))
            authorships_val = parse_json_field(row.get('authorships'))
            related_works_val = parse_json_field(row.get('related_works'))

            publish_date_val = parse_date_field(
                str(row.get('publish_date', '')))
            created_time_val = parse_date_field(
                str(row.get('created_time', '')))

            if isinstance(abstract_val, dict):
                word_positions = []
                for word, positions in abstract_val.items():
                    for pos in positions:
                        if isinstance(pos, int):
                            word_positions.append((pos, word))
                word_positions.sort(key=lambda x: x[0])
                abstract_str = " ".join([w for _, w in word_positions])
            elif isinstance(abstract_val, str) and abstract_val.lower() == "null":
                abstract_str = ""
            else:
                abstract_str = abstract_val if abstract_val else ""

            if isinstance(authorships_val, list):
                authorships_processed = [
                    {"id": author.get("id", ""), "display_name": author.get(
                        "display_name", "")}
                    for author in authorships_val
                ]
            else:
                authorships_processed = []

            if isinstance(research_fields_val, list):
                research_fields_processed = [
                    {"id": field.get("id", ""), "display_name": field.get(
                        "display_name", "")}
                    for field in research_fields_val
                ]
            else:
                research_fields_processed = []

            if isinstance(institutions_val, list):
                institutions_processed = [
                    {"display_name": inst.get(
                        "display_name", ""), "institution_id": inst.get("institution_id", "")}
                    for inst in institutions_val
                ]
            else:
                institutions_processed = []

            doc = {
                "paper_id": doc_id,
                "title": row.get('title', ""),
                "institutions": institutions_processed,
                "publish_date": publish_date_val,
                "journal": row.get('journal', ""),
                "volume": row.get('volume', ""),
                "issue": row.get('issue', ""),
                "doi": row.get('doi', ""),
                "favorites": row.get('favorites', 0),
                "abstract": abstract_str,
                "keywords": keywords_val if keywords_val else [],
                "citation_count": row.get('citation_count', 0),
                "download_link": row.get('download_link', ""),
                "original_link": row.get('original_link', ""),
                "references_works": references_works_val if references_works_val else [],
                "research_fields": research_fields_processed,
                "status": row.get('status', ""),
                "created_time": created_time_val,
                "openalex_paper_id": openalex_id,
                "authorships": authorships_processed,
                "related_works": related_works_val if related_works_val else []
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
            bulk_time = time.time()
            print(f"批量插入 Elasticsearch 用时: {bulk_time - check_time:.2f} 秒")
            print(f"成功迁移 {migrated_count} 条 Paper 数据到 {index_name}")
            print(f"本批次重复数据 {batch_duplicates} 条")
            print(f"累计迁移 {total_migrated} 条 Paper 数据，总共需要迁移 {max_records} 条数据")
            print(f"累计处理数据（成功+重复） {total_processed} 条")
        except es_exceptions.BulkIndexError as e:
            print("BulkIndexError:")
            for error in e.errors:
                print(json.dumps(error, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"迁移 Paper 数据时出错: {str(e)}")

        offset += batch_size
        if max_records is not None and total_migrated >= max_records:
            break

    print("脚本运行成功")


if __name__ == "__main__":
    # 在这里传递具体的参数值，包括偏移量
    migrate_data_to_elasticsearch(
        batch_size=5000, max_records=16000000, offset=5500000)
