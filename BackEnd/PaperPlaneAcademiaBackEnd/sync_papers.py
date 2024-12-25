import os
import django
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
# 设置 Django 的设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PaperPlaneAcademiaBackEnd.settings')

# 初始化 Django 环境
django.setup()

# 初始化 Elasticsearch 连接
es = connections.get_connection()
from papers.models import Paper
from papers.documents import PaperDocument


PaperDocument.init()
# 获取所有 Paper 数据
papers = Paper.objects.all()
actions = []
# 遍历所有数据并推送到 Elasticsearch
for paper in papers:
    doc = PaperDocument(
        meta={'id': paper.paper_id},  # 使用 paper_id 作为文档 ID
        paper_id=paper.paper_id,
        title=paper.title,
        openalex_paper_id=paper.openalex_paper_id,
        authorships=paper.authorships,
        institutions=paper.institutions,
        publish_date=paper.publish_date,
        journal=paper.journal,
        volume=paper.volume,
        issue=paper.issue,
        doi=paper.doi,
        favorites=paper.favorites,
        # abstract=paper.abstract,
        keywords=paper.keywords,
        citation_count=paper.citation_count,
        download_link=paper.download_link,
        original_link=paper.original_link,
        references_works=paper.references_works,
        research_fields=paper.research_fields,
        status=paper.status,
        created_time=paper.created_time,
        remarks=paper.remarks,

    )

    # 将文档对象转为字典并添加到批量操作列表
    actions.append(doc.to_dict(include_meta=True))

# 批量插入数据到 Elasticsearch
if actions:
    success, failed = bulk(es, actions, index=PaperDocument._index._name)
    print(f"Successfully indexed {success} documents, {failed} failed.")

print("Sync complete.")