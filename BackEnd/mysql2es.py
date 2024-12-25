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

# 目标索引名称
index_name = 'papers_index'

def parse_json_field(data):
    """安全解析 JSON 字段，返回 Python 对象（list/dict），如果解析失败则返回空。"""
    if not data:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None

def parse_date_field(date_str):
    """将数据库中的日期或日期时间转换成 Elasticsearch 可识别的字符串。"""
    if not date_str:
        return None
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def fetch_data_from_mysql(limit=None, offset=0):
    """从 MySQL 读取全部数据，支持分页加载。"""
    conn = mysql.connector.connect(**mysql_config)
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM papers_paper"
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return rows

def document_exists(es, index, doc_id):
    """检查文档是否已经存在于 Elasticsearch 中。"""
    try:
        return es.exists(index=index, id=doc_id)
    except es_exceptions.NotFoundError:
        return False

def migrate_data_to_elasticsearch(batch_size=5000):
    """核心迁移逻辑，分批次迁移以减少错误。"""
    es = Elasticsearch(
        hosts=[es_config['host']],
        basic_auth=(es_config['username'], es_config['password'])
    )

    offset = 0
    while True:
        rows = fetch_data_from_mysql(limit=batch_size, offset=offset)
        total = len(rows)
        if total == 0:
            break
        print(f"总共需要迁移 {total} 条数据。")

        actions = []
        for i, row in enumerate(rows, start=1):
            doc_id = row['paper_id']  # 通常用主键作为 _id

            # 检查文档是否已经存在
            if document_exists(es, index_name, doc_id):
                print(f"文档 {doc_id} 已存在，跳过。")
                continue

            # 解析 JSON 字段
            institutions_val = parse_json_field(row.get('institutions'))
            abstract_val = parse_json_field(row.get('abstract'))
            keywords_val = parse_json_field(row.get('keywords'))
            references_works_val = parse_json_field(row.get('references_works'))
            research_fields_val = parse_json_field(row.get('research_fields'))
            authorships_val = parse_json_field(row.get('authorships'))
            related_works_val = parse_json_field(row.get('related_works'))

            # 格式化日期字段
            publish_date_val = parse_date_field(str(row.get('publish_date', '')))
            created_time_val = parse_date_field(str(row.get('created_time', '')))

            # 处理 abstract 字段为字符串
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

            # 处理 authorships 字段为预期格式
            if isinstance(authorships_val, list):
                authorships_processed = [
                    {"id": author.get("id", ""), "display_name": author.get("display_name", "")}
                    for author in authorships_val
                ]
            else:
                authorships_processed = []

            # 处理 research_fields 字段
            if isinstance(research_fields_val, list):
                research_fields_processed = [
                    {"id": field.get("id", ""), "display_name": field.get("display_name", "")}
                    for field in research_fields_val
                ]
            else:
                research_fields_processed = []

            # 处理 institutions 字段
            if isinstance(institutions_val, list):
                institutions_processed = [
                    {"display_name": inst.get("display_name", ""), "institution_id": inst.get("institution_id", "")}
                    for inst in institutions_val
                ]
            else:
                institutions_processed = []

            # 构造文档
            action = {
                "_index": index_name,
                "_id": doc_id,
                "_source": {
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
                    "openalex_paper_id": row.get('openalex_paper_id', ""),
                    "authorships": authorships_processed,
                    "related_works": related_works_val if related_works_val else [],
                }
            }
            actions.append(action)

            # 分批次执行
            if i % batch_size == 0 or i == total:
                try:
                    helpers.bulk(es, actions)
                    print(f"成功迁移前 {i + offset} 条数据到 Elasticsearch 索引 {index_name}！")
                    actions = []
                except es_exceptions.BulkIndexError as e:
                    print(f"第 {i + offset} 条批次 BulkIndexError 详情：")
                    for error in e.errors:
                        print(json.dumps(error, indent=2, ensure_ascii=False))
                        # 可选：将失败文档 ID 写入文件
                        with open('failed_docs.log', 'a') as f:
                            f.write(json.dumps(error, ensure_ascii=False) + '\n')
                    actions = []
                except Exception as e:
                    print(f"迁移第 {i + offset} 条批次过程中发生错误: {str(e)}")
                    actions = []

        offset += batch_size

if __name__ == "__main__":
    migrate_data_to_elasticsearch(batch_size=5000)