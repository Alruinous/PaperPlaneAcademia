# # paper/documents.py
# from django_elasticsearch_dsl import Document, fields, Index
# from django_elasticsearch_dsl.registries import registry
# from .models import Paper  # 假设你的 Paper 模型在同目录下的 models.py

# # 定义一个 ES 索引（名称可根据需要修改，注意小写）
# papers_index = Index('papers_index')

# # 索引的基本设置（分片、副本等）
# papers_index.settings(
#     number_of_shards=1,
#     number_of_replicas=0
# )   

# @registry.register_document
# @papers_index.doc_type
# class PaperDocument(Document):
#     """
#     与数据库表 papers_paper 对应的 Elasticsearch 映射定义。
#     """
#     # 1. paper_id
#     paper_id = fields.IntegerField()

#     # 2. title (longtext) -> ES中用 TextField 进行全文检索
#     title = fields.TextField()

#     # 3. institutions (json) -> 假设里面是一个 list，每个元素含 'display_name'、'institution_id'
#     institutions = fields.NestedField(
#         properties={
#             'display_name': fields.TextField(),
#             'institution_id': fields.TextField(),
#         }
#     )

#     # 4. publish_date (date) -> ES中的 DateField
#     publish_date = fields.DateField()

#     # 5. journal (varchar(1250)) -> 可以直接用 TextField
#     journal = fields.TextField()

#     # 6. volume (varchar(1250)) -> 如果只是纯数字也可存 IntegerField，这里用 TextField 保证灵活
#     volume = fields.TextField()

#     # 7. issue (varchar(1250))
#     issue = fields.TextField()

#     # 8. doi (varchar(1250))
#     doi = fields.TextField()

#     # 9. favorites (int unsigned) -> ES IntegerField
#     favorites = fields.IntegerField()

#     # 10. abstract (json)
#     #   你的示例里 abstract 是一个复杂 dict：{"3": [18], "4": [147], ...}
#     #   若要全文检索并不合适，因为它是键值对结构；如果仅做结构化保存，可以用 ObjectField 或者 NestedField
#     #   这里用 ObjectField 做最基本的存储即可。
#     # abstract = fields.ObjectField()
#     abstract = fields.TextField()

#     # 11. keywords (json) -> 是一个字符串数组，如 ["Purebred", "DNA Methylation", ...]
#     #    所以用 ListField(fields.TextField()) 表示
#     keywords = fields.ListField(fields.TextField())

#     # 12. citation_count (int unsigned)
#     citation_count = fields.IntegerField()

#     # 13. download_link (varchar(1500))
#     download_link = fields.TextField()

#     # 14. original_link (varchar(1500))
#     original_link = fields.TextField()

#     # 15. references_works (json) -> 是一个字符串数组 ["https://openalex.org/W1589013348", ...]
#     references_works = fields.ListField(fields.TextField())

#     # 16. research_fields (json) -> 每个元素有 { "id": "...", "display_name": "..." }
#     research_fields = fields.NestedField(
#         properties={
#             'id': fields.TextField(),
#             'display_name': fields.TextField(),
#         }
#     )

#     # 17. status (varchar(50))
#     status = fields.TextField()

#     # 18. created_time (datetime(6)) -> ES 中使用 DateField 或 DateTimeField
#     created_time = fields.DateField()

#     # 19. openalex_paper_id (longtext)
#     openalex_paper_id = fields.TextField()

#     # 20. authorships (json) -> 数组，每个元素包含 { "id": "...", "display_name": "..." }
#     authorships = fields.NestedField(
#         properties={
#             'id': fields.TextField(),
#             'display_name': fields.TextField(),
#         }
#     )

#     # 21. related_works (json) -> 字符串数组
#     related_works = fields.ListField(fields.TextField())

#     class Django:
#         model = Paper  # 这里要替换成你的 Django 模型名称
#         fields = []    # 因为上面已经显式声明映射，这里不再自动映射字段


# paper/documents.py
from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Paper

# 定义一个新的 ES 索引（名称可根据需要修改，建议使用不同名称）
papers_v2_index = Index('papers_index_v2')

# 索引的基本设置（分片、副本等）
papers_v2_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@registry.register_document
@papers_v2_index.doc_type
class PaperDocument(Document):
    """
    与数据库表 papers_paper 对应的 Elasticsearch 映射定义（新索引）。
    """
    # 1. paper_id
    paper_id = fields.IntegerField()

    # 2. title
    title = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 3. institutions 
    institutions = fields.NestedField(
        properties={
            'display_name': fields.TextField(
                fields={
                    'keyword': fields.KeywordField()
                }
            ),
            'institution_id': fields.TextField(),
        }
    )

    # 4. publish_date
    publish_date = fields.DateField()

    # 5. journal
    journal = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 6. volume
    volume = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 7. issue
    issue = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 8. doi
    doi = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 9. favorites
    favorites = fields.IntegerField()

    # 10. abstract
    abstract = fields.TextField()

    # 11. keywords
    keywords = fields.ListField(
        fields.TextField(
            fields={
                'keyword': fields.KeywordField()
            }
        )
    )

    # 12. citation_count
    citation_count = fields.IntegerField()

    # 13. download_link
    download_link = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 14. original_link
    original_link = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 15. references_works
    references_works = fields.ListField(fields.TextField())

    # 16. research_fields
    research_fields = fields.NestedField(
        properties={
            'id': fields.TextField(),
            'display_name': fields.TextField(
                fields={
                    'keyword': fields.KeywordField()
                }
            ),
        }
    )

    # 17. status
    status = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 18. created_time
    created_time = fields.DateField()

    # 19. openalex_paper_id
    openalex_paper_id = fields.TextField(
        fields={
            'keyword': fields.KeywordField()
        }
    )

    # 20. authorships
    authorships = fields.NestedField(
        properties={
            'id': fields.TextField(),
            'display_name': fields.TextField(
                fields={
                    'keyword': fields.KeywordField()
                }
            ),
        }
    )

    # 21. related_works
    related_works = fields.ListField(fields.TextField())

    class Django:
        model = Paper
        fields = []


