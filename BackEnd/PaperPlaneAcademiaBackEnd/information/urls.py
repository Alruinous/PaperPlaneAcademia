from django.urls import path
from .views import *
from . import views
urlpatterns = [
    
    path("send/",send_information,name="send_information"), # 发送消息
]
