from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from users.models import User
from papers.models import Paper
from comments.models import Comment
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from elasticsearch import Elasticsearch, exceptions as es_exceptions

import json

# 初始化 Elasticsearch 客户端
es_client = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "123456")
)

# Create your views here.
@csrf_exempt
def reply_comments(request,commentId):
    if(request.method=='POST'):
        try:
            comment=Comment.objects.get(comment_id=commentId)

            body = json.loads(request.body)
            userId = body['userId']
            content=body['content']

            user=User.objects.get(user_id=userId)
            newReply=Comment(comment_sender=user,paper=comment.paper,comment_replied=comment,
                             time=timezone.now(),content=content)
            newReply.save()
            comment.replies.append(newReply)

        except Comment.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Comment not found."}, status=404)
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def get_paper_comments(request):
    if(request.method=='POST'):
        try:
            if request.body:
                body = json.loads(request.body)
            else:
                return JsonResponse({"status": "error", "message": "Empty body."}, status=400)
            paperId = body['articleId']
            print(paperId)

            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                        "openalex_paper_id.keyword": paperId  # 精确匹配
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"error": "Paper not found"}, status=404)

            hit = result['hits']['hits'][0]['_source']

            paper_id = hit.get("paper_id", "")

            paper = Paper.objects.get(paper_id=paper_id)
            comments = Comment.objects.filter(paper=paper)


            # 创建一个列表来存储Comment数据
            comments_data=[]

            if comments.exists():
                for comment in comments:
                    replies_data=[]
                    if comment.replies:
                        for reply in comment.replies:
                            replies_data.append({
                                "id": reply.comment_id,
                                "username":reply.comment_sender.username,
                                "content":reply.content,
                            })
                    comments_data.append({
                        "id": comment.comment_id,
                        "username": comment.comment_sender.username,
                        "content": comment.content,
                        "likes": comment.likes,
                        "replies":replies_data,
                        "avator":comment.comment_sender.avatar
                    })

            return JsonResponse({"success": "true",
                                 "comments": comments_data
                                })
        except Paper.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Paper not found."}, status=404)
        
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def like_comments(request):
    if(request.method == 'POST'):
        try:
            body = json.loads(request.body)
            commentId = body['commentId']
            comment=Comment.objects.get(comment_id=commentId)
            comment.likes+=1
            comment.save()

            return JsonResponse({"success":"true", "likes":comment.likes})
        except Comment.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Comment not found."}, status=404)
        

@csrf_exempt
def publish_comments(request):
    if(request.method == 'POST'):
        try:
            body = json.loads(request.body)
            print(body)
            paperId = body['paperId']
            userId  = body['userId']
            content=body['content']

            sender=User.objects.get(user_id=userId)
            if sender is None:
                return JsonResponse({"status":"error", "message":"评论者ID不存在!"})
            
            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                        "openalex_paper_id.keyword": paperId  # 精确匹配
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"error": "Paper not found"}, status=404)

            hit = result['hits']['hits'][0]['_source']

            paper_id = hit.get("paper_id", "")

            paper = Paper.objects.get(paper_id=paper_id)

            newComment = Comment(comment_sender=sender, paper=paper, time=timezone.now(), content=content)
            newComment.save()

            return JsonResponse({"success":"true", "commentId":newComment.comment_id})
        
        except User.DoesNotExist:
            return JsonResponse({"status":"error", "message":"User not found."})
        except Paper.DoesNotExist:
            return JsonResponse({"status":"error", "message":"Paper not found."})

        except Exception as e:
            print(e)
            return JsonResponse({"success":"false", "message":str(e)})

