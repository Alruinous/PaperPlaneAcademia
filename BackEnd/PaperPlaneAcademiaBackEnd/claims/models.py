from django.db import models
from papers.models import Paper
from users.models import User
from authors.models import Author


# Create your models here.
class Claim(models.Model):
    claim_id = models.AutoField(primary_key=True)  # 认领申请的唯一标识符
    claim_sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='claim_sender')  # 关联用户模块
    claim_author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='claim_author', null=True)  # 申请认证的学者
    send_time = models.DateTimeField(auto_now_add=True)  # 申请的发送时间
    process_time = models.DateTimeField(auto_now_add=True)  # 申请的处理时间
    # 申请的当前状态 Pending / Approved / Rejected
    status = models.CharField(max_length=50, default="Pending")
    
