from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Topic  # 确保正确导入Topic模型

# 定义索引名称
topics_index = Index('topics_index_v1')
topics_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
@topics_index.doc_type
class TopicDocument(Document):
    topic_id = fields.IntegerField()
    openalex_topic_id = fields.TextField(fields={'keyword': fields.KeywordField()})
    display_name = fields.TextField(fields={'keyword': fields.KeywordField()})
    works_count = fields.IntegerField()
    cited_by_count = fields.IntegerField()
    description = fields.TextField()

    # keywords 为字符串数组，使用 ListField
    keywords = fields.ListField(
        fields.TextField(fields={'keyword': fields.KeywordField()})
    )

    # siblings 为嵌套对象数组，包含 id 和 display_name
    siblings = fields.NestedField(
        properties={
            'id': fields.TextField(fields={'keyword': fields.KeywordField()}),
            'display_name': fields.TextField(fields={'keyword': fields.KeywordField()})
        }
    )

    # topic_papers 为嵌套对象数组，根据实际数据结构调整
    topic_papers = fields.NestedField(
        properties={
            # 根据实际结构定义字段
            # 例如，如果每个 paper 包含 paper_id 和 title
            'paper_id': fields.IntegerField(),
            'title': fields.TextField(fields={'keyword': fields.KeywordField()})
        }
    )

    class Django:
        model = Topic  # 指定关联的Django模型
        fields = []   # 其他非显式定义的字段