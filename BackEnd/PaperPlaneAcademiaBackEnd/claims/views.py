from elasticsearch import Elasticsearch, exceptions as es_exceptions
from elasticsearch_dsl import Search, Q as ES_Q
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from users.models import User
from papers.models import Paper
from claims.models import Claim
from authors.models import Author
from institutions.models import Institution
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from django.core.cache import cache

import json

# 初始化 Elasticsearch 客户端
es_client = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "123456")
)

# Create your views here.
@csrf_exempt
def search_author(request):
    if(request.method == 'POST'):
        try:
            # 从请求体中解析 JSON 数据
            body = json.loads(request.body)
            print(body)
            author_names = body.get('authorNames', [])   # 获取作者名称数组
            institutionName=body.get('organization')        # 获取机构名称
            #print(author_names[0])

            # 使用 Elasticsearch 查询 authors 中的多个作者
            if not author_names:
                return JsonResponse({"error": "Missing 'authorNames' parameter"}, status=400)
           
            # 使用 Elasticsearch 查询 authors 中的多个作者
            result = es_client.search(
                index='authors_index_v1',  # 使用最新的索引
                body={
                    "_source": "*",  # 获取所有字段
                    "query": {
                        "bool": {
                        "should": [
                            {
                                "terms": {
                                    "name.keyword": author_names  # 在 name.keyword 字段中查找匹配的作者名称
                                }
                            },
                            {
                                "terms": {
                                    "name_alternatives.keyword": author_names  # 在 name_alternatives.keyword 字段中查找匹配的作者名称
                                }
                            }
                        ],
                        "minimum_should_match": 1  # 至少匹配一个作者名称
                    }
                    }
                }
            )
            #return JsonResponse({"message": ['hits']['hits'][0]['_source']}, status=200)
            # 检查是否有匹配学者
            if not result['hits']['hits']:
                return JsonResponse({"matched_scholars": []}, status=200)

            all_authors_info=[]
            for hit in result['hits']['hits']:
                author_hit = hit['_source']

                openalex_author_id=author_hit.get('openalex_author_id')
                # 获取作者相关论文，使用 keyword 字段进行精确匹配
                search_papers = Search(index='papers_index_v2').filter(
                    'nested',
                    path='authorships',
                    query={'term': {'authorships.id.keyword': openalex_author_id}}
                ).source(['title']).extra(size=1000)  # 根据需要调整 size 和 source
                response_papers = search_papers.execute()

                papers_title = []   # 构建文章数据
                for hit in response_papers:
                    hit_dict = hit.to_dict()
                    papers_title.append({"title": hit_dict.get("title", "")})

                all_authors_info.append({
                    "name":author_hit.get('name'),
                    "Id":author_hit.get('openalex_author_id'),
                    "authorOrganization":', '.join(sorted(set(institution['display_name'] for institution in author_hit.get('last_known_institutions') or []))),
                    "papers":papers_title
                })
                
            return JsonResponse({"success": "true", "matched_scholars": all_authors_info})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
            '''
            # 查找与机构名称匹配的机构: 使用 icontains 进行模糊匹配
            matched_institution = Institution.objects.filter(display_name__icontains=institutionName) 

            # 创建一个列表存储匹配的学者信息
            matched_scholars = []

            # 遍历每个匹配的机构
            for institution in matched_institution:
                # 假设 openalex_institution_id 是你用来索引的字段
                openalex_institution_id = institution.openalex_institution_id  
                print(openalex_institution_id)

                # 从 Redis 缓存中查找对应机构的学者列表
                redis_key = f'institution:{openalex_institution_id}'
                scholars_data = cache.get(redis_key)

                print(scholars_data)

                # 如果缓存中有数据，进行筛选
                if scholars_data:
                    for scholar in scholars_data:
                        # 检查 scholar['name'] 和 scholar['name_alternatives'] 是否匹配 authorNames
                        scholar_name = scholar['name']
                        scholar_name_alternatives = scholar.get('name_alternatives', [])

                        # 检查 scholar_name 或者 scholar_name_alternatives 中是否有匹配的名称
                        if any(author_name.lower() in scholar_name.lower() for author_name in author_names) or \
                           any(author_name.lower() in alt_name.lower() for author_name in author_names for alt_name in scholar_name_alternatives):
                            matched_scholars.append({
                                "Id": scholar.author_id,
                                "name":scholar.name,
                                "authorOrganization":institution.display_name,
                            })

                else:
                    # 获取所有符合条件的作者
                    authors = Author.objects.filter(
                        # 遍历每个 author 的 last_known_institutions 列表，查找匹配的 institution_id
                        last_known_institutions__contains=[{
                            "institution_id": openalex_institution_id
                        }]
                    )
                    author=authors.first()
                    # 当前学者的所有paper
                    papers=Paper.objects.filter(
                        authorships__contains=[{
                            "id": author.author_id
                        }]
                    )
                    papers_name=[paper.title for paper in papers]
                    print(papers_name)

                    matched_scholars.append({
                        "Id": author.author_id,
                        "name":author.name,
                        "authorOrganization":institution.display_name,
                        "papers":papers_name,
                    })
                    
            '''
        

# 用户发起学者身份的认领
@csrf_exempt
def authenticate_claim(request):
    if(request.method == 'POST'):
        try:
            body = json.loads(request.body)
            name = body['name']
            otherName=body['otherName']
            gender=body['gender']
            email=body['email']
            selectedScholarId=body['selectedScholarId']
            userId=body['userId']

            sender=User.objects.get(user_id=userId)
            
            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='authors_index_v1',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            "openalex_author_id.keyword": selectedScholarId  # 精确匹配
                        }
                    }
                }
            )
            # 检查是否有匹配学者
            if not result['hits']['hits']:
                return JsonResponse({"error": "Author not found"}, status=404)
            
            hit = result['hits']['hits'][0]['_source']
            author_id=hit.get('author_id')
            
            author=Author.objects.get(author_id=author_id)

            newClaim=Claim(claim_sender=sender, claim_author=author)
            newClaim.save()

            return JsonResponse({"status": "success", "message": "Claim submitted."}, status=200)

        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        

@csrf_exempt
def get_all_claims(request):
    if request.method == 'GET':
        try:
            claims = Claim.objects.all().order_by('-send_time')  # 使用 `-` 表示降序排序
            # 创建一个列表来存储Claim数据
            claims_data=[]
            for claim in claims:
                claims_data.append({
                    "id": claim.claim_id,
                    "username": claim.claim_sender.username,
                    "email": claim.claim_sender.email,
                    "organization": claim.claim_paper.institutions,
                    "content": claim.claim_paper.title,  # 论文标题
                    "apply_time":claim.send_time,
                    "claimID":claim.claim_id
                })

            # 计算总记录数
            total_claims = claims.count()
            # 构造返回的JSON数据
            response_data = {
                "status": "success",
                "data": {
                    "claims": claims_data,
                    "total": total_claims
                }
            }
            # 返回JsonResponse，自动将Python字典转换为JSON格式
            return JsonResponse(response_data)
            
        except Claim.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
        except Exception as e:
            # 如果发生错误，返回错误信息
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
@csrf_exempt
def approve_claim(request,claimID):
    if(request.method == 'POST'):
        try:
            claim=Claim.objects.get(claim_id=claimID)
        
            claim.status = 'Approved'
            claim.process_time=timezone.now()
            claim.save()  # 保存更改

            return JsonResponse({"status":"success", "message":"操作成功"})
        except Claim.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
        

@csrf_exempt
def reject_claim(request,claimID):
    if(request.method == 'POST'):
        try:
            claim=Claim.objects.get(claim_id=claimID)
        
            claim.status = 'Rejected'
            claim.process_time=timezone.now()
            claim.save()  # 保存更改

            return JsonResponse({"status":"success", "message":"操作成功"})
        except Claim.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
        

@csrf_exempt
def get_all_applications(request):
    if request.method == "GET":
        try:
            claims = Claim.objects.filter(status="Pending")
            message_claims = []
            message_total = 0

            for claim in claims:
                message_claims.append({
                    "id": claim.claim_id,
                    "name": claim.claim_sender.username,
                    "email": claim.claim_sender.email,
                    "institution": claim.claim_sender.institution,
                    "selectScholarId": claim.claim_author.openalex_author_id,
                    "userId": claim.claim_sender.user_id
                })
                message_total += 1

            return JsonResponse({"status": "success", 
                                 "data": {
                                    "claims": message_claims, 
                                    "total": message_total
                                    }
                                })
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
@csrf_exempt
def approve_application(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            applicationId = body['applicationId']
            claim = Claim.objects.get(claim_id=applicationId)
            claim.status = "Approved"
            claim.claim_sender.research_fields = claim.claim_author.topics
            claim.claim_sender.author_claimed = claim.claim_author
            claim.claim_sender.user_type = 'researcher'

            claim.claim_sender.save()
            claim.save()

            return JsonResponse({"status": "success", "message": "同意成功"})

        except Claim.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
@csrf_exempt
def reject_application(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            applicationId = body['applicationId']
            claim = Claim.objects.get(claim_id=applicationId)
            claim.status = "Rejected"
        
            claim.save()

            return JsonResponse({"status": "success", "message": "拒绝成功"})

        except Claim.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Claim not found."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)