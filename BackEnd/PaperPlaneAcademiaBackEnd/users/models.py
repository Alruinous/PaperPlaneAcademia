from django.db import models
from papers.models import Paper
from authors.models import Author


class User(models.Model):
    user_id = models.AutoField(primary_key=True)  # 用户的唯一标识符
    username = models.CharField(max_length=255, unique=True)  # 用户的登录名
    password = models.CharField(max_length=255)  # 用户的密码（加密存储）
    email = models.EmailField(unique=True)  # 用户的电子邮箱
    institution = models.CharField(
        max_length=255, null=True, blank=True)  # 用户所属机构
    user_type = models.CharField(max_length=50, choices=[(
        'researcher', '科研人员'), ('reviewer', '审核人员'), ('normalUser', '普通用户')])  # 用户类型
    bio = models.TextField(null=True, blank=True)  # 用户的个人介绍
    research_fields = models.JSONField(null=True, blank=True)  # 用户的研究领域
    avatar = models.IntegerField(default=0)  # 用户选择的头像
    published_papers_count = models.PositiveIntegerField(
        default=0)  # 用户发表的论文数量
    uploaded_papers = models.ManyToManyField(
        Paper, related_name='uploaded_by', blank=True)  # 用户已发表的论文列表
    favorite_papers = models.ManyToManyField(
        Paper, related_name='favorited_by', blank=True)  # 用户收藏的论文
    recent_viewed_papers = models.ManyToManyField(
        Paper, related_name='recently_viewed_by', blank=True)  # 最近浏览的论文
    followers = models.ManyToManyField(
        'self', related_name='following', symmetrical=False, blank=True)  # 用户的粉丝列表
    inbox = models.JSONField(null=True, blank=True)  # 收件箱（可选字段）
    register_time = models.DateTimeField(auto_now_add=True)  # 用户的注册时间
    status = models.CharField(
        max_length=50, default='active')  # 用户的账户状态（如正常、禁用等）
    remarks = models.TextField(null=True, blank=True)  # 额外备注说明
    # 关联 Author 模型的外键，可以为空
    author_claimed = models.ForeignKey(
        Author, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_by')  # 外键，允许为空

    def __str__(self):
        return self.username
