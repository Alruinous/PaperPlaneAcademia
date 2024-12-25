from django.urls import path
from .views import *
from . import views
urlpatterns = [
    # path("", get_all_claims, name='get_all_claims'),
    # path('<int:claimID>/approve/', approve_claim, name="approve_claim"),
    # path('<int:claimID>/reject/', reject_claim, name="reject_claim"),
    path('authentication/',authenticate_claim, name="authenticate_claim"),
    #path('fetchscholars/',search_author, name="search_author"), # 认领学者身份时，查询当前名称对应的所有可能学者
    path('applications/', get_all_applications, name="get_all_applications"),
    path('applications/approve/', approve_application, name="approve_application"),
    path('applications/reject/', reject_application, name="reject_application"),
     
    path('fetchscholars/',search_author, name="search_author"), # 认领学者身份时，查询当前名称对应的所有可能学者
]
