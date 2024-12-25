from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Author  # 假设已存在 Author 模型

authors_index = Index('authors_index_v1')  # 根据需要命名索引

authors_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@registry.register_document
@authors_index.doc_type
class AuthorDocument(Document):
    author_id = fields.IntegerField()
    openalex_author_id = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )
    orcid = fields.TextField()
    name = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )
    name_alternatives = fields.ListField(
        fields.TextField(
            fields={
                'keyword': fields.KeywordField()
            }
        )
    )
    works_count = fields.IntegerField()
    cited_by_count = fields.IntegerField()
    h_index = fields.IntegerField()
    two_yr_mean_citedness = fields.IntegerField()
    two_yr_cited_by_count = fields.IntegerField()
    last_known_institutions = fields.NestedField(
        properties={
            'country_code': fields.TextField(),
            'display_name': fields.TextField(
                fields={'keyword': fields.KeywordField()}
            ),
            'institution_id': fields.TextField()
        }
    )
    topics = fields.NestedField(
        properties={
            'topic_id': fields.TextField(),
            'topic_name': fields.TextField(
                fields={'keyword': fields.KeywordField()}
            ),
            'value': fields.FloatField()
        }
    )

    class Django:
        model = Author
        fields = []
