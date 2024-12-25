from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from users.models import User
from papers.models import Paper
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import User
from comments.models import Comment

import json



def extract_display_names(data):
    """
    提取每个对象的 display_name 属性，返回一个新的字符串列表。

    :param data: 输入的数据，应该是一个字典列表，每个字典包含 display_name 属性。
    :return: 包含所有 display_name 的字符串列表。
    """
    # 使用列表推导式来提取 display_name
    return [item.get('display_name', '') for item in data]

def extract_topic_name(data):
    """
    提取Author的topics属性中的topic_name, 拼接成字符串列表
    [
        {
        "value": 0.0000049, 
        "topic_id": "https://openalex.org/T11146", 
        "topic_name": "Long-Term Effects of Testosterone on Health"
        }
    ]
    """
    return [item.get('topic_name', '') for item in data]



@csrf_exempt
def changeFavorate(request):
    if (request.method == 'POST'):
        try:
            body = json.loads(request.body)
            userid = body['userid']
            paperid = body['paperid']
            flag = body['flag']

            user = User.objects.get(user_id=userid)
            paper = Paper.objects.get(paper_id=paperid)

            # 判断flag的值，进行相应的操作
            if flag == 0:
                user.favorite_papers.add(paper)  # 添加收藏
            elif flag == 1:
                user.favorite_papers.remove(paper)  # 从收藏中移除
            else:
                # 如果flag不是0或1，可以根据需要抛出异常或返回错误信息
                raise JsonResponse({"status": "error", "message": "Invalid flag value, must be 0 or 1"}, status=500)

        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found."}, status=404)
        except Paper.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Paper not found."}, status=404)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def login(request):
    if (request.method == 'POST'):
        body = json.loads(request.body)
        username = body['username']
        password = body['password']
        try:
            user = User.objects.get(username=username)  # 没查到会抛出 DoesNotExist异常
            correct_password = user.password
            if (password == correct_password):
                return JsonResponse({"status": "success",
                                     "UserId": user.user_id,
                                     "username": user.username,
                                     "avatarId": user.avatar
                                     })
            else:
                return JsonResponse({"status": "error", "message": "密码错误"})

        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "当前用户还未注册!"})


@csrf_exempt
def register(request):
    if (request.method == 'POST'): 
        body = json.loads(request.body)
        username = body['username']
        password = body['password']
        email = body['email']
        organization = body['organization']
        avatarIndex = body['avatar']

        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": "error", "message": "当前用户已存在!"})

        if User.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "当前邮箱已注册!"})

        newUser = User(
            username=username,
            password=password,
            email=email,
            institution=organization,
            user_type = 'normalUser',
            avatar = avatarIndex,
            research_fields = []
        )
        newUser.save()

        return JsonResponse({"status": "success", "message": "注册成功!"})


@csrf_exempt
def platform_overview(request):
    if request.method == 'GET':
        try:
            user_number = User.objects.count()
            # paper_number = Paper.objects.count()
            author_number = User.objects.filter(user_type='researcher').count()
            # reviewer_number = User.objects.filter(user_type='reviewer').count()

            return JsonResponse({"status": "success",
                                 "data": {
                                     "totalUsers": user_number,
                                    #  "totalPapers": paper_number,
                                    #  "totalAuthors": author_number,
                                     "totalScholars": author_number
                                 }
                                 })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def get_scholars(request):
    if request.method == 'GET':
        try:
            # 查询所有科研人员用户
            scholars = User.objects.filter(user_type='researcher')

            # 构造返回数据
            scholar_data = [
                {
                    "username": scholar.username,
                    "email": scholar.email,
                    "organization": scholar.institution or "未提供",  # 如果机构为空，显示“未提供”
                    "joinedAt": scholar.register_time.strftime('%Y-%m-%d'),  # 格式化日期
                    "publications": scholar.published_papers_count
                }
                for scholar in scholars
            ]

            response_data = {
                "status": "success",
                "data": {
                    "scholars": scholar_data,
                    "total": scholars.count()
                }
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    else:
        return JsonResponse({"status": "error", "message": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def updateResearchFields(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_id = body['userId']
            research_fields = body['researchFields']  # 是个列表，我要改成json格式存入数据库{"field1":"...", "field2":"..."}
            research_fields_JSON = {}
            for i in range(1, len(research_fields) + 1):
                research_fields_JSON[f"field{i}"] = research_fields[i - 1]

            user = User.objects.get(user_id=user_id)
            user.research_fields = research_fields_JSON
            user.save()
            return JsonResponse({"success": True, "message": "研究领域更新成功"})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "当前用户不存在"})
        except Exception as e:
            return JsonResponse({"success": False, "message": "更新失败，请检查输入"})


@csrf_exempt
def updateDescription(request):
    if request.method == 'POST':
        print("dlafjalsdkjf")
        try:
            body = json.loads(request.body)
            user_id = body['userId']
            bio = body['description']

            user = User.objects.get(user_id=user_id)
            user.bio = bio
            user.save()
            return JsonResponse({"success": True, "message": "简介更新成功"})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "当前用户不存在"})
        except Exception as e:
            return JsonResponse({"success": False, "message": "失败"})

@csrf_exempt
def get_my_user_data(request):
    try:
        body = json.loads(request.body)
    
        user_id = body['userId']  # 从查询参数中获取 userId
        if not user_id:
            return JsonResponse({'error': 'userId is required'}, status=400)
        
        user = User.objects.get(user_id = user_id)  # 获取用户对象，找不到则返回 404 错误
        is_authenticated = user.user_type != 'normalUser'
        
        print(user)
        # print(is_authenticated)
        # 获取用户基本信息
        user_info = {
            "name": user.username,
            "photoUrl": user.avatar,
            "description": user.bio,
            "researchFields": ', '.join(extract_topic_name(user.research_fields) or []),
            "registerTime": user.register_time.strftime('%Y-%m-%d'),
            "institution": user.institution,
            "status": user.status,
            "papersCount": user.published_papers_count,
            "email": user.email,
            "phoneNumber": getattr(user, 'phone', '未提供'),  # 如果模型中没有 phone 字段则默认 '未提供'
            "followingCount": user.following.count(),
            "followerCount": user.followers.count()
        }
        

        # 获取用户收藏的论文信息
        favorite_articles = [
            {
                "id": paper.openalex_paper_id,
                "title": paper.title,
                "authors": ', '.join(extract_display_names(paper.authorships)),
                "institutions": ', '.join([institution.get('display_name', '') for institution in paper.institutions] or []),
                "journal": paper.journal,
                "publishTime": paper.publish_date.strftime('%Y-%m-%d'),
                "doi": paper.doi,
                "citationCount": paper.citation_count,
                "favoriteCount": paper.favorites
            }
            for paper in user.favorite_papers.all()
        ]

        # 获取用户发表的评论信息
        comments = [
            {
                "commenter": comment.comment_sender.username,
                "paperId": comment.paper.paper_id,
                "paperTitle":comment.paper.title,
                "time": comment.time.strftime('%Y-%m-%d %H:%M'),
                "content": comment.content,
                "likeCount": comment.likes
            }
            for comment in Comment.objects.filter(comment_sender=user)
        ]

        # 获取用户上传的论文信息
        articles = [
            {
                "id": paper.paper_id,
                "title": paper.title,
                "authors": ', '.join(extract_display_names(paper.authorships)), 
                "institutions": ', '.join(paper.institutions or []),
                "journal": paper.journal,
                "publishTime": paper.publish_date.strftime('%Y-%m-%d'),
                "doi": paper.doi,
                "citationCount": paper.citation_count,
                "favoriteCount": paper.favorites
            }
            for paper in user.uploaded_papers.all()
        ]

        return JsonResponse({
            "userInfo": user_info,
            "isAuthenticated": is_authenticated,
            "favoriteArticles": favorite_articles,
            "comments": comments,
            "articles": articles
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# 更改用户关注状态-> 关注改成取消关注，取消关注改成关注
@csrf_exempt
def get_other_user_data(request):
    body = json.loads(request.body)
    user_id = body['userId']  # 从查询参数中获取 userId
    current_user_id = body['currentUserId']
    print(user_id)
    print(current_user_id)

    if not user_id:
        return JsonResponse({'error': 'userId is required'}, status=400)

    user = get_object_or_404(User, pk=user_id)  # 获取用户对象，找不到则返回 404 错误
    # 检查是否已关注
    is_followed = False
    if current_user_id:
        current_user = get_object_or_404(User, pk=current_user_id)
        is_followed = current_user.following.filter(pk=user_id).exists()
    # 获取用户基本信息
    user_info = {
        "name": user.username,
        "photoUrl": user.avatar,
        "description": user.bio,
        "researchFields": ', '.join(user.research_fields or []),
        "registerTime": user.register_time.strftime('%Y-%m-%d'),
        "institution": user.institution,
        "status": user.status,
        "papersCount": user.published_papers_count,
        "email": user.email,
        "phoneNumber": getattr(user, 'phone', '未提供'),  # 如果模型中没有 phone 字段则默认 '未提供'
        "followingCount": user.following.count(),
        "followerCount": user.followers.count()
    }

    # 获取用户收藏的论文信息
    favorite_articles = [
        {
            "id": paper.paper_id,
            "title": paper.title,
            "authors": ', '.join(paper.authorships),
            "institutions": ', '.join(paper.institutions or []),
            "journal": paper.journal,
            "publishTime": paper.publish_date.strftime('%Y-%m-%d'),
            "doi": paper.doi,
            "citationCount": paper.citation_count,
            "favoriteCount": paper.favorites
        }
        for paper in user.favorite_papers.all()
    ]

    # 获取用户发表的评论信息
    comments = [
        {
            "commenter": comment.comment_sender.username,
            "paperId": comment.paper.paper_id,
            "time": comment.time.strftime('%Y-%m-%d %H:%M'),
            "content": comment.content,
            "likeCount": comment.likes
        }
        for comment in Comment.objects.filter(comment_sender=user)
    ]

    # 获取用户上传的论文信息
    articles = [
        {
            "id": paper.paper_id,
            "title": paper.title,
            "authors": ', '.join(paper.authorships),
            "institutions": ', '.join(paper.institutions or []),
            "journal": paper.journal,
            "publishTime": paper.publish_date.strftime('%Y-%m-%d'),
            "doi": paper.doi,
            "citationCount": paper.citation_count,
            "favoriteCount": paper.favorites
        }
        for paper in user.uploaded_papers.all()
    ]

    return JsonResponse({
        "userInfo": user_info,
        "favoriteArticles": favorite_articles,
        "comments": comments,
        "articles": articles,
        "isFollowed": is_followed  # 添加 isFollowed 字段
    })


@csrf_exempt
def change_follow(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            current_user_id = body['currentUserId']
            target_user_id = body['targetUserId']

            current_user = User.objects.get(user_id=current_user_id)
            target_user = User.objects.get(user_id=target_user_id)

            # 当前用户的关注列表
            if current_user.following.filter(user_id=target_user_id).exists():
                current_user.following.remove(target_user)
                return JsonResponse({"success": True, "message": "取消关注成功"})
            else:
                current_user.following.add(target_user)
                return JsonResponse({"success": True, "message": "关注成功"})


        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "当前用户或目标用户不存在"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})


@csrf_exempt
def updateAvatar(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_id = body['userId']
            avatar = body['avatarIndex']
            user = User.objects.get(user_id=user_id)
            user.avatar = avatar
            user.save()
            return JsonResponse({"status": True, "message": "头像更新成功"})

        except User.DoesNotExist:
            return JsonResponse({"status": False, "message": "当前用户不存在"})
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
