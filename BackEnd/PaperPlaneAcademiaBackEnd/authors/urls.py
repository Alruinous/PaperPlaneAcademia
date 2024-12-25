from django.urls import path
from .views import *
from . import views

urlpatterns = [
    # path("search/", search_paper, name='search_paper'),
    path('getpage/', get_author_page_count, name='get_author_page_count'),
    path('searchscholars/', search_scholars, name='search_scholars'),
    path('scholarData/', scholar_data, name='scholar_data'),
]
