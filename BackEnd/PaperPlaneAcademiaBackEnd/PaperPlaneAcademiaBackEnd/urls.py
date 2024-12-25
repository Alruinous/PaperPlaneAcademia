"""
URL configuration for PaperPlaneAcademiaBackEnd project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('users.urls')),  # 将 'user/' 映射到 users 应用的路由
    path('search/', include('papers.urls')),  # 包含 'papers' 应用的 URL 配置
    path('papers/', include('papers.urls')),  # 后期要改
    path('users/', include('users.urls')),
    path('claims/', include('claims.urls')),
    path('comment/', include('comments.urls')),
    path('paper/', include('papers.urls')),
    path('information/', include('information.urls')),
    path('information/', include('information.urls')),  # 信息模块
    path('field/', include('topics.urls')),  # 学科模块
    path('authors/', include('authors.urls')),
    path('author/', include('authors.urls')),
]
