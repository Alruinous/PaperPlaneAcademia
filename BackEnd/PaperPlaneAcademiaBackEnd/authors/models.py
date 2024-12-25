from django.db import models


# Create your models here.
class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    openalex_author_id = models.TextField()  # 学者的OpenAlex ID
    orcid = models.TextField()  # 该作者的 ORCID（开放研究者和贡献者标识符）
    name = models.TextField()  # 作者姓名
    name_alternatives = models.JSONField(null=True, blank=True)  # 该作者可能使用的其他展示名称
    works_count = models.IntegerField(default=0)  # 发表的总学术作品数量
    cited_by_count = models.IntegerField(default=0)  # 所有作品被引用的总次数
    h_index = models.IntegerField(default=0)  # H-index
    two_yr_mean_citedness = models.IntegerField(default=0)  # 过去两年该作者作品的平均被引用次数
    two_yr_cited_by_count = models.IntegerField(default=0)  # 过去两年内该作者的作品被引用的总次数
    # 存储机构的ID及相关信息，例如：[{ "institution_id": "institution_id_1", "years": [2020, 2021] }, ...]
    last_known_institutions = models.JSONField(null=True, blank=True)
    # 存储主题的ID及相关值，例如：[{ "topic_id": "topic_id_1", "value": 0.75 }, ...]
    topics = models.JSONField(null=True, blank=True)
