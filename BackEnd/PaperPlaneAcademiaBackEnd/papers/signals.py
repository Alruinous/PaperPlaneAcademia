from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Paper
from .documents import PaperDocument


# 保存时同步到 Elasticsearch
@receiver(post_save, sender=Paper)
def update_paper_in_elasticsearch(sender, instance, created, **kwargs):
    """
    论文数据保存时，更新 Elasticsearch 索引。
    - 如果是新创建的 Paper 对象，则创建 Elasticsearch 索引。
    - 如果是更新的 Paper 对象，则更新 Elasticsearch 中的文档。
    """
    if created:
        # 如果是新创建的论文，初始化 Elasticsearch 索引
        PaperDocument.init()  # 确保索引已经创建
    # 更新或创建 Elasticsearch 中的文档
    doc = PaperDocument(meta={'id': instance.paper_id})
    doc.update(instance)


# 删除时同步删除 Elasticsearch 中的文档
@receiver(post_delete, sender=Paper)
def delete_paper_from_elasticsearch(sender, instance, **kwargs):
    """
    论文数据删除时，从 Elasticsearch 中删除相应的文档。
    """
    PaperDocument(meta={'id': instance.paper_id}).delete()
