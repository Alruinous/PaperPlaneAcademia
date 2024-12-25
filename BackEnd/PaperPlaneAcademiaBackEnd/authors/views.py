import math
import random
from django.core.cache import cache
from django.core.cache import cache  # 确保正确导入缓存
from datetime import datetime
from elasticsearch_dsl import Search
from django.shortcuts import render
from elasticsearch_dsl import Search, Q as ES_Q
from elasticsearch import Elasticsearch

from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
from functools import lru_cache

from .models import Author
from users.models import User
from comments.models import Comment
from papers.models import Paper
from institutions.models import Institution
from topics.models import Topic


@csrf_exempt
def get_author_page_count(request):
    try:
        # 从请求体获取 searchConditions
        body = json.loads(request.body)
        search_conditions = body.get('searchConditions', [])

        # 构建查询条件
        query = Q()

        # 处理各字段为空的情况
        for condition in search_conditions:
            # 如果 value 为空，则设置为 None
            value = condition.get('value', '').strip() or None
            operator = condition.get('operator', None)
            # 如果 scope 为空，则设置为 None
            scope = condition.get('scope', '').strip() or None

            # 检查并跳过无效的条件
            if not value or not scope:
                continue  # 如果 value 或 scope 为空，则跳过该条件

            # 根据 scope 字段确定查询字段
            if scope == 'name':
                query_field = 'name'
            elif scope == 'organization':
                query_field = 'last_known_institutions__display_name'
            elif scope == 'field':
                query_field = 'topics__topic_name'
            else:
                continue  # 如果 scope 不符合要求，则跳过该条件

            # 构建具体的查询条件
            condition_query = Q(**{f'{query_field}__icontains': value})

            # 根据逻辑操作符进行条件叠加
            if operator == 'OR':
                query |= condition_query  # OR 连接
            elif operator == 'NOT':
                query &= ~condition_query  # NOT 连接
            else:
                query &= condition_query  # 默认是 AND 连接

        # 使用构建的查询条件进行查询
        total_authors = Author.objects.filter(query)

        # 计算总页数，每页 10 条
        total_count = total_authors.count()
        total_pages = (total_count + 9) // 10  # 向上取整

        return JsonResponse({'page': total_pages})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# @csrf_exempt
# def search_scholars(request):
#     try:
#         body = json.loads(request.body)
#         search_conditions = body.get('searchConditions', [])
#         sort = body.get('sort', 1)
#         page = body.get('page', 1)

#         if not isinstance(sort, int) or not isinstance(page, int):
#             return JsonResponse({'error': 'Invalid sort or page parameter'}, status=400)

#         # 构建查询条件
#         query = Q()

#         # 处理 searchConditions
#         for condition in search_conditions:
#             value = condition.get('value', '').strip() or None  # 如果 value 为空，则设置为 None
#             operator = condition.get('operator', None)
#             scope = condition.get('scope', '').strip() or None

#             if not value or not scope:
#                 continue  # 如果 value 或 scope 为空，则跳过该条件

#             # 根据 scope 字段确定查询字段
#             if scope == 'name':
#                 query_field = 'name'
#             elif scope == 'organization':
#                 query_field = 'last_known_institutions__display_name'
#             elif scope == 'field':
#                 query_field = 'topics__topic_name'
#             else:
#                 continue  # 如果 scope 不符合要求，则跳过该条件

#             # 构建查询条件
#             condition_query = Q(**{f'{query_field}__icontains': value})

#             # 根据逻辑操作符进行条件叠加
#             if operator == 'OR':
#                 query |= condition_query  # OR 连接
#             elif operator == 'NOT':
#                 query &= ~condition_query  # NOT 连接
#             else:
#                 query &= condition_query  # 默认是 AND 连接

#         # 使用构建的查询条件进行查询
#         authors = Author.objects.filter(query)

#         # 排序
#         if sort == 1:
#             # 相关度排序：这里可以自定义相关度计算方法，根据条件匹配程度排序
#             authors = sorted(authors, key=lambda x: calculate_relevance(x, search_conditions), reverse=True)
#         elif sort == 2:
#             # 按论文数排序，正序或倒序
#             authors = authors.order_by('-works_count' if sort < 0 else 'works_count')

#         # 分页处理，10条一页
#         start_index = (page - 1) * 10
#         end_index = start_index + 10
#         authors_page = authors[start_index:end_index]

#         # 构建返回数据
#         result = []
#         for author in authors_page:
#             # 获取学者的相关信息
#             fields = [
#                 {"fieldname": topic["topic_name"], "fieldId": topic["topic_id"]}
#                 for topic in author.topics or []
#             ]

#             organization = ''
#             if author.last_known_institutions:
#                 organization = author.last_known_institutions[0].get('display_name', '')

#             # 获取该作者的所有合作者
#             collaborators = get_collaborators(author)

#             result.append({
#                 "Id": author.openalex_author_id,
#                 "name": author.name,
#                 "fields": fields,
#                 "organization": organization,
#                 "paperCount": str(author.works_count),
#                 "collaborators": collaborators
#             })

#         return JsonResponse({'authors': result})

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)


# @csrf_exempt
# def scholar_data(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

#     try:
#         body = json.loads(request.body)
#         openalex_author_id = body.get("authorId")
#         if not openalex_author_id:
#             return JsonResponse({"error": "Missing 'authorId' in request body"}, status=400)

#         # 查询作者
#         try:
#             author = Author.objects.get(openalex_author_id=openalex_author_id)
#         except Author.DoesNotExist:
#             return JsonResponse({"error": "Author not found"}, status=404)

#         # 解析作者信息
#         user_info = {
#             "name": author.name,
#             "institution": [inst["display_name"] for inst in (author.last_known_institutions or [])],
#             "orcid": author.orcid,
#             "alternative_names": author.name_alternatives or [],
#             "works_count": author.works_count,
#             "cited_count": author.cited_by_count,
#             "institution_country": [inst["country_code"] for inst in (author.last_known_institutions or [])]
#         }

#         # 获取作者相关论文
#         papers = Paper.objects.filter(authorships__contains=[{"id": openalex_author_id}])
#         articles = []
#         for paper in papers:
#             articles.append({
#                 "id": paper.openalex_paper_id,
#                 "title": paper.title,
#                 "authors": [auth["display_name"] for auth in (paper.authorships or [])],
#                 "institutions": [inst["display_name"] for inst in (paper.institutions or [])],
#                 "journal": paper.journal,
#                 "publishTime": paper.publish_date,
#                 "doi": paper.doi,
#                 "citationCount": paper.citation_count,
#                 "favoriteCount": paper.favorites
#             })

#         # 获取合作者
#         experts = []
#         for paper in papers:
#             for auth in paper.authorships or []:
#                 if auth["id"] != openalex_author_id:  # 排除当前作者
#                     experts.append({"id": auth["id"], "name": auth["display_name"]})

#         # 去重合作者
#         unique_experts = {expert["id"]: expert for expert in experts}.values()

#         response_data = {
#             "userInfo": user_info,
#             "articles": articles,
#             "experts": list(unique_experts),
#             "contributions": get_contributions(author)

#         }
#         return JsonResponse(response_data, safe=False, status=200)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

####正确的
@csrf_exempt
def scholar_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        body = json.loads(request.body)
        openalex_author_id = body.get("authorId")
        if not openalex_author_id:
            return JsonResponse({"error": "Missing 'authorId' in request body"}, status=400)

        cache_key = f"scholar_data:{openalex_author_id}"
        cached_response = cache.get(cache_key)
        if cached_response:
            print("Cache hit! Returning scholar data from cache.")
            return JsonResponse(cached_response, safe=False, status=200)

        # 查询作者信息，使用 keyword 字段进行精确匹配
        search_author = Search(index='authors_index_v1').filter(
            'term', **{"openalex_author_id.keyword": openalex_author_id}
        ).source([
            'name',
            'last_known_institutions.display_name',
            'last_known_institutions.country_code',
            'orcid',
            'name_alternatives',
            'works_count',
            'cited_by_count',
            'topics'
        ]).extra(size=1)
        response_author = search_author.execute()

        if not response_author.hits:
            return JsonResponse({"error": "Author not found"}, status=404)

        author_hit = response_author.hits[0].to_dict()

        # 解析作者信息
        user_info = {
            "name": author_hit.get("name", ""),
            "institution": [inst.get("display_name", "") for inst in author_hit.get("last_known_institutions", [])],
            "orcid": author_hit.get("orcid", ""),
            "alternative_names": author_hit.get("name_alternatives", []),
            "works_count": author_hit.get("works_count", 0),
            "cited_count": author_hit.get("cited_by_count", 0),
            "institution_country": [inst.get("country_code", "") for inst in author_hit.get("last_known_institutions", [])]
        }

        # 获取作者相关论文，使用 keyword 字段进行精确匹配
        search_papers = Search(index='papers_index_v2').filter(
            'nested',
            path='authorships',
            query={
                'match_phrase': {
                    'authorships.id': openalex_author_id
                }
            }
        ).source([
            'openalex_paper_id',
            'title',
            'authorships.display_name',
            'authorships.id',
            'institutions.display_name',
            'journal',
            'publish_date',
            'doi',
            'citation_count',
            'favorites'
        ]).extra(size=1000)  # 根据需要调整 size 和 source
        response_papers = search_papers.execute()

        articles = []
        experts = []
        for hit in response_papers:
            hit_dict = hit.to_dict()

            # 处理 authorships
            authorships = hit_dict.get('authorships', [])
            authors = []
            for auth in authorships:
                authors.append({
                    "userName": auth.get("display_name", ""),
                    "userId": auth.get("id", "")
                })
                if auth.get("id") != openalex_author_id:
                    experts.append({"id": auth.get("id", ""),
                                   "name": auth.get("display_name", "")})

            # 处理 publish_date
            publish_date_str = hit_dict.get('publish_date', "")
            publish_date = None
            if isinstance(publish_date_str, str):
                try:
                    # 尝试解析完整的日期时间格式
                    publish_date = datetime.strptime(
                        publish_date_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    try:
                        # 尝试解析仅日期部分
                        publish_date = datetime.strptime(
                            publish_date_str, "%Y-%m-%d")
                    except ValueError:
                        publish_date = None
            elif isinstance(publish_date_str, datetime):
                publish_date = publish_date_str

            year = str(publish_date.year) if isinstance(
                publish_date, datetime) else "N/A"

            # 构建文章数据
            articles.append({
                "id": hit_dict.get("openalex_paper_id", ""),
                "title": hit_dict.get("title", ""),
                "authors": [auth.get("display_name", "") for auth in authorships],
                "institutions": [inst.get("display_name", "") for inst in hit_dict.get("institutions", [])],
                "journal": hit_dict.get("journal", ""),
                "publishTime": publish_date_str if publish_date_str else "",
                "doi": hit_dict.get("doi", ""),
                "citationCount": hit_dict.get("citation_count", 0),
                "favoriteCount": hit_dict.get("favorites", 0)
            })

        # 获取合作者并去重
        unique_experts = list(
            {expert["id"]: expert for expert in experts if expert["id"]}.values()
        )

        # 获取贡献信息
        contributions = get_contributions(
            author_hit)  # 修改后的 get_contributions 接受字典

        response_data = {
            "userInfo": user_info,
            "articles": articles,
            "experts": unique_experts,
            "contributions": contributions
        }

        # 将响应数据存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
        cache.set(cache_key, response_data, timeout=7200)

        return JsonResponse(response_data, safe=False, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
### 正确的
# def generate_random_ids(openalex_author_id, count=5):
#     random.seed(openalex_author_id)  # 使用 openalex_author_id 作为随机种子
#     return [random.randint(50000, 1000000) for _ in range(count)]


# def get_authors_from_es(author_ids):
#     query = {
#         "query": {
#             "terms": {
#                 "author_id": author_ids
#             }
#         }
#     }
#     response = es.search(index='authors_index', body=query)
#     return response['hits']['hits']


# def update_experts(openalex_author_id):
#     experts = []
#     random_ids = generate_random_ids(
#         openalex_author_id, count=random.randint(5, 20))
#     authors = get_authors_from_es(random_ids)
#     for auth in authors:
#         experts.append({"id": auth['_source'].get(
#             "id", ""), "name": auth['_source'].get("display_name", "")})
#     return experts


# @csrf_exempt
# def scholar_data(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

#     try:
#         body = json.loads(request.body)
#         openalex_author_id = body.get("authorId")
#         if not openalex_author_id:
#             return JsonResponse({"error": "Missing 'authorId' in request body"}, status=400)

#         cache_key = f"scholar_data:{openalex_author_id}"
#         cached_response = cache.get(cache_key)
#         if cached_response:
#             print("Cache hit! Returning scholar data from cache.")
#             return JsonResponse(cached_response, safe=False, status=200)

#         # 查询作者信息，使用 keyword 字段进行精确匹配
#         search_author = Search(index='authors_index_v1').filter(
#             'term', **{"openalex_author_id.keyword": openalex_author_id}
#         ).source([
#             'name',
#             'last_known_institutions.display_name',
#             'last_known_institutions.country_code',
#             'orcid',
#             'name_alternatives',
#             'works_count',
#             'cited_by_count',
#             'topics'
#         ]).extra(size=1)
#         response_author = search_author.execute()

#         if not response_author.hits:
#             return JsonResponse({"error": "Author not found"}, status=404)

#         author_hit = response_author.hits[0].to_dict()

#         # 解析作者信息
#         user_info = {
#             "name": author_hit.get("name", ""),
#             "institution": [inst.get("display_name", "") for inst in author_hit.get("last_known_institutions", [])],
#             "orcid": author_hit.get("orcid", ""),
#             "alternative_names": author_hit.get("name_alternatives", []),
#             "works_count": author_hit.get("works_count", 0),
#             "cited_count": author_hit.get("cited_by_count", 0),
#             "institution_country": [inst.get("country_code", "") for inst in author_hit.get("last_known_institutions", [])]
#         }

#         # 获取作者相关论文，使用 keyword 字段进行精确匹配
#         search_papers = Search(index='papers_index_v2').filter(
#             'nested',
#             path='authorships',
#             query={'term': {'authorships.id.keyword': openalex_author_id}}
#         ).source([
#             'openalex_paper_id',
#             'title',
#             'authorships.display_name',
#             'authorships.id',
#             'institutions.display_name',
#             'journal',
#             'publish_date',
#             'doi',
#             'citation_count',
#             'favorites'
#         ]).extra(size=1000)  # 根据需要调整 size 和 source
#         response_papers = search_papers.execute()

#         articles = []
#         experts = []
#         for hit in response_papers:
#             hit_dict = hit.to_dict()

#             # 处理 authorships
#             authorships = hit_dict.get('authorships', [])
#             authors = []
#             for auth in authorships:
#                 authors.append({
#                     "userName": auth.get("display_name", ""),
#                     "userId": auth.get("id", "")
#                 })
#                 if auth.get("id") != openalex_author_id:
#                     experts.append({"id": auth.get("id", ""),
#                                    "name": auth.get("display_name", "")})

#             # 处理 publish_date
#             publish_date_str = hit_dict.get('publish_date', "")
#             publish_date = None
#             if isinstance(publish_date_str, str):
#                 try:
#                     # 尝试解析完整的日期时间格式
#                     publish_date = datetime.strptime(
#                         publish_date_str, "%Y-%m-%dT%H:%M:%S")
#                 except ValueError:
#                     try:
#                         # 尝试解析仅日期部分
#                         publish_date = datetime.strptime(
#                             publish_date_str, "%Y-%m-%d")
#                     except ValueError:
#                         publish_date = None
#             elif isinstance(publish_date_str, datetime):
#                 publish_date = publish_date_str

#             year = str(publish_date.year) if isinstance(
#                 publish_date, datetime) else "N/A"

#             # 构建文章数据
#             articles.append({
#                 "id": hit_dict.get("openalex_paper_id", ""),
#                 "title": hit_dict.get("title", ""),
#                 "authors": [auth.get("display_name", "") for auth in authorships],
#                 "institutions": [inst.get("display_name", "") for inst in hit_dict.get("institutions", [])],
#                 "journal": hit_dict.get("journal", ""),
#                 "publishTime": publish_date_str if publish_date_str else "",
#                 "doi": hit_dict.get("doi", ""),
#                 "citationCount": hit_dict.get("citation_count", 0),
#                 "favoriteCount": hit_dict.get("favorites", 0)
#             })

#         # 获取合作者并去重
#         unique_experts = list(
#             {expert["id"]: expert for expert in experts if expert["id"]}.values()
#         )

#         # 如果 experts 为空，则使用伪造算法生成
#         if not unique_experts:
#             unique_experts = update_experts(openalex_author_id)

#         # 获取贡献信息
#         contributions = get_contributions(
#             author_hit)  # 修改后的 get_contributions 接受字典

#         response_data = {
#             "userInfo": user_info,
#             "articles": articles,
#             "experts": unique_experts,
#             "contributions": contributions
#         }

#         # 将响应数据存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
#         cache.set(cache_key, response_data, timeout=7200)

#         return JsonResponse(response_data, safe=False, status=200)

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)




# 计算学者与查询条件的相关度


def calculate_relevance(author, search_conditions):
    relevance = 0
    for condition in search_conditions:
        value = condition.get('value', '').strip().lower()
        scope = condition.get('scope', '').strip().lower()

        if scope == 'name' and value in author.name.lower():
            relevance += 1
        elif scope == 'organization':
            for institution in author.last_known_institutions or []:
                if value.lower() in institution.get('display_name', '').lower():
                    relevance += 1
        elif scope == 'field':
            for topic in author.topics or []:
                if value.lower() in topic.get('topic_name', '').lower():
                    relevance += 1

    return relevance


# 初始化 Elasticsearch 客户端（启用连接池）
es = Elasticsearch(
    ['http://localhost:9200'],  # 根据实际情况调整地址
    maxsize=25  # 根据并发需求调整
)


# @csrf_exempt
# def search_scholars(request):
#     try:
#         body = json.loads(request.body)
#         search_conditions = body.get('searchConditions', [])
#         sort = body.get('sort', 1)
#         page = body.get('page', 1)

#         if not isinstance(sort, int) or not isinstance(page, int):
#             return JsonResponse({'error': 'Invalid sort or page parameter'}, status=400)

#         # 构建 Elasticsearch 查询
#         es_query = ES_Q('bool', must=[], should=[], must_not=[])

#         for condition in search_conditions:
#             value = condition.get('value', '').strip()
#             operator = condition.get('operator', '').strip().upper()
#             scope = condition.get('scope', '').strip().lower()

#             if not value or not scope:
#                 continue

#             if scope == 'name':
#                 query_field = 'name.keyword'
#             elif scope == 'organization':
#                 query_field = 'last_known_institutions.display_name.keyword'
#             elif scope == 'field':
#                 query_field = 'topics.topic_name.keyword'
#             else:
#                 continue

#             match_query = {
#                 "match_phrase": {
#                     query_field: value
#                 }
#             }

#             if operator == 'OR':
#                 es_query['bool']['should'].append(match_query)
#             elif operator == 'NOT':
#                 es_query['bool']['must_not'].append(match_query)
#             else:
#                 es_query['bool']['must'].append(match_query)

#         # 构建搜索对象
#         s = Search(using=es, index='authors_index_v1').query(es_query)

#         # 排序
#         if sort == 1:
#             # 相关度排序，默认按 Elasticsearch 的 _score 排序
#             s = s.sort({'_score': {'order': 'desc'}})
#         elif sort == -1:
#             # 相关度升序
#             s = s.sort({'_score': {'order': 'asc'}})
#         elif sort == 2:
#             # 按论文数排序，倒序
#             s = s.sort({'works_count': {'order': 'desc'}})
#         elif sort == -2:
#             # 按论文数排序，升序
#             s = s.sort({'works_count': {'order': 'asc'}})
#         elif sort == 3:
#             # 按时间排序，倒序
#             s = s.sort({'publish_date': {'order': 'desc'}})
#         elif sort == -3:
#             # 按时间排序，升序
#             s = s.sort({'publish_date': {'order': 'asc'}})

#         # 分页处理
#         s = s[(page - 1) * 10: page * 10]

#         response = s.execute()

#         result = []
#         author_ids = [hit.openalex_author_id for hit in response]

#         # 批量获取合作作者，减少数据库查询次数
#         collaborators_dict = get_bulk_collaborators(author_ids)

#         for hit in response:
#             # 使用属性访问而非字典访问
#             topics = hit.topics if hasattr(hit, 'topics') else []
#             fields = [{"fieldname": topic.topic_name,
#                        "fieldId": topic.topic_id} for topic in topics]

#             last_known_institutions = hit.last_known_institutions if hasattr(
#                 hit, 'last_known_institutions') else []
#             organization = last_known_institutions[0].display_name if last_known_institutions else ''

#             # 获取合作者
#             collaborators = collaborators_dict.get(hit.openalex_author_id, [])

#             result.append({
#                 "Id": hit.openalex_author_id,
#                 "name": hit.name,
#                 "fields": fields,
#                 "organization": organization,
#                 "paperCount": str(hit.works_count),
#                 "collaborators": collaborators
#             })

#         return JsonResponse({'authors': result})

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)

def get_bulk_collaborators(author_ids):
    """
    根据作者ID列表批量获取合作者信息，这里示例返回空或模拟数据。
    真实实现中可根据实际需求查询数据库或其他索引。
    """
    return {aid: [] for aid in author_ids}


es = Elasticsearch(['http://localhost:9200'])


@csrf_exempt
def search_scholars(request):
    try:
        body = json.loads(request.body)
        search_conditions = body.get('searchConditions', [])
        sort = body.get('sort', 1)
        page = body.get('page', 1)

        if not isinstance(sort, int) or not isinstance(page, int):
            return JsonResponse({'error': 'Invalid sort or page parameter'}, status=400)

        # 构建 Elasticsearch 查询
        must_queries = []
        should_queries = []
        must_not_queries = []
        tmplogic = 'AND'
        if len(search_conditions) > 1:
            tmplogic = search_conditions[1].get('logic').strip().lower()
        for condition in search_conditions:
            logic = (condition.get('logic') or '').strip().lower()
            value = (condition.get('value') or '').strip()
            scope = (condition.get('scope') or '').strip().lower()
            # 跳过空条件
            if not value or not scope:
                continue

            # 根据 scope 决定查询的字段
            if scope == 'name':
                # 改为对 "name" 字段使用 match 查询，实现分词搜索
                field = 'name'
            elif scope == 'organization':
                # 同理，使用 "last_known_institutions.display_name" 进行 match 查询
                field = 'last_known_institutions.display_name'
            elif scope == 'field':
                field = 'topics.topic_name'
            else:
                continue

            # 改用 match，如果需要更精准的短语匹配可改为 match_phrase
            part = ES_Q("match", **{field: value})

            if not logic:
                logic = tmplogic

            # 根据 logic 分配到 must/should/must_not
            if logic == 'or':
                should_queries.append(part)
            elif logic == 'not':
                must_not_queries.append(part)
            else:
                must_queries.append(part)

        # 构建 bool 查询
        es_query = ES_Q('bool', must=must_queries,
                        should=should_queries, must_not=must_not_queries)
        print("构建的查询条件:", es_query)

        # 发起查询
        s = Search(using=es, index='authors_index_v1').query(es_query)

        # 排序
        if sort == 1:
            s = s.sort({'_score': {'order': 'desc'}})
        elif sort == -1:
            s = s.sort({'_score': {'order': 'asc'}})
        elif sort == 2:
            s = s.sort({'works_count': {'order': 'desc'}})
        elif sort == -2:
            s = s.sort({'works_count': {'order': 'asc'}})
        elif sort == 3:
            s = s.sort({'cited_by_count': {'order': 'desc'}})
        elif sort == -3:
            s = s.sort({'cited_by_count': {'order': 'asc'}})

        # 分页
        page_size = 10
        # 向上取整计算总页数
        total_pages = math.ceil(s.count() / page_size)

        start = (page - 1) * page_size
        end = page * page_size
        s = s[start:end]
        response = s.execute()
        query_time = response.took  # 查询耗时（毫秒）
        author_ids = [hit.openalex_author_id for hit in response]
        print("author_ids:", author_ids)

        # 如果没有结果，返回空数组
        if not author_ids:
            return JsonResponse([], safe=False, status=200)

        # 构建作者与合作者的映射
        collaborators_map = {}

        for aid in author_ids:
            # 针对每个作者，用其 openalex_author_id 去 paper 索引中匹配相关论文
            single_author_papers = Search(index='papers_index_v2').filter(
                'nested',
                path='authorships',
                query={'term': {'authorships.id.keyword': aid}}
            ).source(['authorships.id', 'authorships.display_name'])

            result_paper = single_author_papers.execute()
            collaborators_map[aid] = set()

            # 遍历该作者的每篇论文，获取合作者
            for paper_hit in result_paper:
                paper_authors = paper_hit.authorships or []
                for co_author in paper_authors:
                    # 如果不是当前作者，则将其加入合作者集合
                    if co_author.id != aid:
                        collaborators_map[aid].add(
                            (co_author.id, co_author.display_name))

        # 将 set 转为列表
        for aid in collaborators_map:
            collaborators_map[aid] = [{"id": cid, "name": cname}
                                      for cid, cname in collaborators_map[aid]]

        # 构建返回结果
        result = []
        for hit in response:
            topics = getattr(hit, 'topics', [])
            insts = getattr(hit, 'last_known_institutions', [])
            org = insts[0].display_name if insts else ''
            fields = [{"fieldname": t.topic_name, "fieldId": t.topic_id}
                      for t in topics]

            # 获取该作者的合作者列表
            collaborators = collaborators_map.get(hit.openalex_author_id, [])

            result.append({
                "Id": hit.openalex_author_id,
                "name": hit.name,
                "fields": fields,
                "organization": org,
                "paperCount": str(hit.works_count),
                "collaborators": collaborators,
                "time": 0 #es查询时间 token
            })

        return JsonResponse({"result": result, "totalPages": total_pages, "queryTime": query_time}, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@lru_cache(maxsize=1024)
def fetch_author_topics(openalex_author_id):
    """
    从 Elasticsearch 获取作者的 topics，并缓存结果。
    """
    try:
        response = es.search(
            index="authors_index_v1",
            body={
                "query": {
                    "term": {
                        "openalex_author_id.keyword": openalex_author_id
                    }
                },
                "_source": ["topics"]
            },
            size=1
        )
        if response["hits"]["hits"]:
            return response["hits"]["hits"][0]["_source"].get("topics", [])
    except Exception:
        pass
    return []


def get_collaborators(openalex_author_id):
    collaborators = {}
    # 假设 authorships 是一个列表，包含字典，每个字典有 'id' 和 'display_name'
    papers = Paper.objects.filter(
        authorships__contains=[{"id": openalex_author_id}])
    for paper in papers:
        for author_info in paper.authorships or []:
            if author_info.get('id') != openalex_author_id:
                collaborators[author_info['id']] = {
                    "name": author_info.get('display_name', ''),
                    "id": author_info.get('id', '')
                }
    return list(collaborators.values())


def get_contributions(author):
    """
    根据作者的 topics 字段生成 contributions 数据，
    移除循环中的多余打印，使用 fetch_author_topics 做缓存。
    """
    openalex_author_id = author.get("openalex_author_id", "")
    # 从缓存或 Elasticsearch 获取 topics
    topics = fetch_author_topics(
        openalex_author_id) or author.get("topics", []) or []
    contributions = []
    for topic in topics:
        contributions.append({
            "id": topic.get("topic_id"),
            "display_name": topic.get("topic_name"),
            "domain": topic.get("topic_name"),
            "value": str(topic.get("value", ""))
        })
    return contributions


# def get_bulk_collaborators(author_ids):
#     """
#     批量获取多个作者的合作者，减少数据库查询次数。
#     """
#     collaborators_dict = {author_id: [] for author_id in author_ids}
#     # 获取所有相关的论文
#     papers = Paper.objects.filter(authorships__contains=[{"id": author_id} for author_id in author_ids]).distinct()

#     for paper in papers:
#         authorships = paper.authorships or []
#         for author_info in authorships:
#             author_id = author_info.get('id')
#             if author_id in collaborators_dict:
#                 for collaborator in authorships:
#                     collaborator_id = collaborator.get('id')
#                     if collaborator_id and collaborator_id != author_id:
#                         collaborator_name = collaborator.get('display_name', '')
#                         if not any(c['id'] == collaborator_id for c in collaborators_dict[author_id]):
#                             collaborators_dict[author_id].append({
#                                 "name": collaborator_name,
#                                 "id": collaborator_id
#                             })
#     return collaborators_dict
