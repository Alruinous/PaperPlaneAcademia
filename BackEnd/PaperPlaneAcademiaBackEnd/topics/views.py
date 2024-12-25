from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import Topic
from elasticsearch import Elasticsearch, exceptions as es_exceptions

import json
# Create your views here.


# 初始化 Elasticsearch 客户端
es_client = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "123456")
)

@csrf_exempt
def getField(request):
    try:
        if request.method == 'GET':
            id = request.GET.get('id')

            # 使用 Elasticsearch 查询 openalex_topic_id.keyword
            result = es_client.search(
                index='topics_index_v1',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            "openalex_topic_id.keyword": id  # 精确匹配
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"message": "Topic not found"}, status=404)


            hit = result['hits']['hits'][0]['_source']

            topic_id = hit.get("topic_id", 0)
            topic = Topic.objects.get(topic_id=topic_id)

            if topic is None:
                return JsonResponse({'status': 'false'}, status=404)
            return_message = {
                "status": "true",
                "field": {
                    "name": topic.display_name,
                    "worksCount": topic.works_count,
                    "citedCount": topic.cited_by_count,
                    "description": topic.description,
                    "keywords": topic.keywords,
                    "siblings": topic.siblings
                }
            }

            return JsonResponse(return_message)
    except Topic.DoesNotExist:
        return JsonResponse({'status': 'false'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
