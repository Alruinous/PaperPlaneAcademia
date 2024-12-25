from django.db import models


# Create your models here.
# 科研领域
class Topic(models.Model):
    topic_id = models.AutoField(primary_key=True)
    openalex_topic_id = models.TextField()  # Topic的OpenAlex ID
    display_name = models.CharField(max_length=255)
    works_count = models.IntegerField(default=0)  # 主题的论文数量
    cited_by_count = models.IntegerField(default=0)  # 主题的论文被引用次数
    description = models.TextField()  # 主题的描述信息
    keywords = models.JSONField()  # 主题的关键词列表: 使用 JSON 字段存储关键词列表
    siblings = models.JSONField()  # 同级主题关系: 使用 JSON 字段存储兄弟主题列表
    topic_papers=models.JSONField(blank=True, null=True)    # 当前领域下的所有论文

    # 定义一个方法来返回可读的主题名称
    def __str__(self):
        return self.display_name

    class Meta:
        # 添加元数据，使模型可以按名称进行排序
        ordering = ['display_name']
