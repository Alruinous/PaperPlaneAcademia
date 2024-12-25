from django.urls import path
from .views import *
from . import views

urlpatterns = [
    # path("search/", search_paper, name='search_paper'),
    path('', search_paper, name='home'),  # 访问根路径时显示 search_paper 视图
    path('getArticle/', views.get_article, name='get_article'),
    path('top/', get_top_papers, name='get_top_papers'),
    path('recommended/', get_recommended_papers, name='get_recommended_papers'),
    path('statistics/', get_statistics, name='get_statistics'),
    path('searchbyname/', search_papers_by_name, name='search_papers_by_name'),
    path('simple/', simple_search_papers, name='simple_search_papers'),
    path('search/', advanced_search_papers, name='advanced_search_papers'),
    path('getStar/', get_if_starPaper, name='get_if_starPaper'),
    path('postStar/', post_starPaper, name='post_starPaper'),
    path('filterdata/', filter_data, name='filter_data'),
    path('getpage/', get_page, name='get_page'),
    path('organizations/', hotest_organizations, name='hotest_organizations'),
    path('fields/', hotest_fields, name='hotest_fields'),
    path('starCnt/', getStarCnt, name='getStarCnt'),
]
