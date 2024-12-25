import json
import mysql.connector
from elasticsearch import Elasticsearch, helpers, exceptions as es_exceptions
from datetime import datetime

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

index_name = 'authors_index_v1'


def parse_json_field(data):
    if not data:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def fetch_author_data(limit=None, offset=0):
    conn = mysql.connector.connect(**mysql_config)
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM authors_author ORDER BY author_id ASC"
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return rows


def document_exists(es, index, doc):
    """检查文档是否已经存在于 Elasticsearch 中"""
    query = {
        "query": {
            "term": {
                "openalex_author_id.keyword": doc["openalex_author_id"]
            }
        }
    }
    response = es.search(index=index, body=query)
    return response['hits']['total']['value'] > 0


def migrate_author_data(batch_size, max_records, offset=0):
    es = Elasticsearch(
        hosts=[es_config['host']],
        basic_auth=(es_config['username'], es_config['password'])
    )

    total_migrated = 0
    print(f"总共需要迁移 {max_records} 条 Author 数据")

    while True:
        rows = fetch_author_data(limit=batch_size, offset=offset)
        if not rows:
            break
        if max_records is not None and total_migrated >= max_records:
            break
        if max_records is not None:
            remaining = max_records - total_migrated
            if remaining < batch_size:
                rows = rows[:remaining]

        actions = []
        for row in rows:
            doc_id = row['author_id']
            name_alts = parse_json_field(row.get('name_alternatives'))
            institutions = parse_json_field(row.get('last_known_institutions'))
            topics_val = parse_json_field(row.get('topics'))

            doc = {
                "author_id": doc_id,
                "openalex_author_id": row.get('openalex_author_id', ""),
                "orcid": row.get('orcid', ""),
                "name": row.get('name', ""),
                "name_alternatives": name_alts if name_alts else [],
                "works_count": row.get('works_count', 0),
                "cited_by_count": row.get('cited_by_count', 0),
                "h_index": row.get('h_index', 0),
                "two_yr_mean_citedness": row.get('two_yr_mean_citedness', 0),
                "two_yr_cited_by_count": row.get('two_yr_cited_by_count', 0),
                "last_known_institutions": institutions if institutions else [],
                "topics": topics_val if topics_val else []
            }

            # 检查文档是否已经存在
            if document_exists(es, index_name, doc):
                print(f"文档已存在，跳过 author_id: {doc_id}")
                continue

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
            print(f"成功迁移 {migrated_count} 条 Author 数据到 {index_name}")
            print(f"累计迁移 {total_migrated} 条 Author 数据，总共需要迁移 {max_records} 条数据")
        except es_exceptions.BulkIndexError as e:
            print("BulkIndexError:")
            for error in e.errors:
                print(json.dumps(error, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"迁移 Author 数据时出错: {str(e)}")

        offset += batch_size
        if max_records is not None and total_migrated >= max_records:
            break

    print("脚本运行成功")


if __name__ == "__main__":
    # 在这里传递具体的参数值，包括偏移量
    migrate_author_data(batch_size=10000, max_records=5000000, offset=0)