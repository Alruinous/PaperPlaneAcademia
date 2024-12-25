from django.db import models
from papers.models import Paper
from users.models import User

class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)  # 评论的唯一标识符
    comment_sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_comments')  # 关联用户模块
    paper = models.ForeignKey(
        Paper, on_delete=models.CASCADE, related_name='comments')  # 关联论文模块
    comment_replied = models.ForeignKey(
    'Comment', on_delete=models.CASCADE, related_name='target_comment',blank=True,null=True)  # 当前评论的回复对象
    replies = models.JSONField(null=True, blank=True)  # 当前评论的回复列表
    time = models.DateTimeField(auto_now_add=True)  # 评论的发表时间
    likes = models.PositiveIntegerField(default=0)  # 评论的点赞次数
    content = models.TextField()  # 评论的具体内容

    def __str__(self):
        return f'Comment by {self.comment_sender} on {self.paper}'
