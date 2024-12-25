from django.db import models
from users.models import User


class Information(models.Model):
    info_id = models.AutoField(primary_key=True)  # 信息的唯一标识符
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_informations')  # 信息的发送者
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_informations')  # 信息的接收者
    send_time = models.DateTimeField(auto_now_add=True)  # 信息的发送时间
    is_read = models.BooleanField(default=False)  # 信息是否已被阅读
    title = models.CharField(max_length=255)  # 信息的标题
    content = models.TextField()  # 信息的正文内容

    def __str__(self):
        return f'Information from {self.sender} to {self.receiver}'
