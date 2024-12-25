from django.urls import path
from . import views
from .views import *

urlpatterns = [
    #path('scholars', get_scholars, name='get_scholars'),  # 对应接口 /users/scholars
    #path('userData', get_user_data, name='get_user_data'),
    path('login/', login, name='login'), #用户登录
    path('register/', register, name='register'), #用户注册
    path('scholars/', get_scholars, name='get_scholars'),  # 对应接口 /users/scholars
    path('platform-overview/', platform_overview, name='platform_overview'),
    path('updateResearchFields/', updateResearchFields, name='updateResearchFields'),
    path('updateDescription/', updateDescription, name='updateDescription'),
    path('follow/', change_follow, name='change_follow'),
    path('myUserData/', get_my_user_data, name='get_my_user_data'),
    path('otherUserData/', get_other_user_data, name='get_other_user_data'),
    path('login/', login, name='login'), #用户登录
    path('register/', register, name='register'), #用户注册
    path('scholars/', get_scholars, name='get_scholars'),  # 对应接口 /users/scholars
    path('platform-overview/', platform_overview, name='platform_overview'), # 对应接口 /users/platform-overview
    path('updateResearchFields/', updateResearchFields, name='updateResearchFields'), # 对应接口 /users/updateResearchFields
    path('updateDescription/', updateDescription, name='updateDescription'), # 对应接口 /users/updateDescription
    path('favorate/',changeFavorate,name="change-favorate"), # 用户收藏论文
    path('updateAvatar/', updateAvatar, name='updateAvatar'), # 更新用户头像


]
