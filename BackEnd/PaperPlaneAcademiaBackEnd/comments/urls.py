from django.urls import path
from .views import *
from . import views
urlpatterns = [
    path("publish/", publish_comments, name='publish_comments'),    # 发表评论
    path("like/",like_comments, name="like_comments"),  # 点赞评论
    path("getComment/",get_paper_comments,name="get_paper_comments"), # 获取评论列表
    path("<int:commentId>/reply/",reply_comments, name="reply_comments"),   # 回复评论
]
