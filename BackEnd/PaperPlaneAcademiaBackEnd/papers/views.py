from elasticsearch import Elasticsearch, exceptions as es_exceptions
import json
import hashlib
from itertools import zip_longest
from collections import Counter
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_elasticsearch_dsl.search import Search  # 导入 Search 类
from users.models import User
from comments.models import Comment
from .documents import PaperDocument  # 导入你定义的 Elasticsearch 文档类
from .models import Paper
from institutions.models import Institution
from topics.models import Topic
from django.db.models import Q
from datetime import datetime
from math import ceil
from django.db.models import Count, Case, When, IntegerField

from django.core.cache import cache


def transform_to_author_format(data):
    """
    将数据转换成目标格式，生成包含 id 和 authorName 的字典列表。

    :param data: 输入的原始数据列表，每个字典包含 id 和 display_name 属性
    :return: 转换后的字典列表，每个字典包含 id 和 authorName
    """
    # 直接提取 id 和 display_name，创建目标格式的字典
    return [{"id": item.get('id', ''), "authorName": item.get('display_name', '')} for item in data]


def transform_to_field_format(data):
    """
    将数据转换成目标格式，生成包含 id 和 authorName 的字典列表。

    :param data: 输入的原始数据列表，每个字典包含 id 和 display_name 属性
    :return: 转换后的字典列表，每个字典包含 id 和 authorName
    """
    # 直接提取 id 和 display_name，创建目标格式的字典
    return [{"id": item.get('id', ''), "name": item.get('display_name', '')} for item in data]


def extract_display_names(data):
    """
    提取每个对象的 display_name 属性，返回一个新的字符串列表。

    :param data: 输入的数据，应该是一个字典列表，每个字典包含 display_name 属性。
    :return: 包含所有 display_name 的字符串列表。
    """
    # 使用列表推导式来提取 display_name
    return [item.get('display_name', '') for item in data]


# def process_abstract_to_string(abstract_data):
#     """
#     将倒排索引形式的 abstract 数据转换为普通的字符串。
#     :param abstract_data: dict，倒排索引形式的摘要
#     :return: str，普通字符串形式
#     """
#     # if not isinstance(abstract_data, dict):
#     #     raise ValueError("Input abstract_data must be a dictionary.")

#     # if not isinstance(abstract_data, dict):
#     #     raise ValueError("Input abstract_data must be a dictionary.")

#     if not abstract_data:  # 检查 abstract_data 是否为空
#         return ""
#     # 按出现顺序恢复原始的摘要字符串
#     words_with_positions = []
#     for word, positions in abstract_data.items():
#         for position in positions:
#             words_with_positions.append((position, word))

#     # 按照位置排序
#     words_with_positions.sort(key=lambda x: x[0])

#     # 拼接成字符串
#     result = " ".join(word for _, word in words_with_positions)
#     print(result)
#     return result


# # 保存时同步到 Elasticsearch


@csrf_exempt
@receiver(post_save, sender=Paper)
def update_paper_in_elasticsearch(sender, instance, created, **kwargs):
    """
    论文数据保存时，更新 Elasticsearch 索引。
    - 如果是新创建的 Paper 对象，则创建 Elasticsearch 索引。
    - 如果是更新的 Paper 对象，则更新 Elasticsearch 中的文档。
    """
    if created:
        # 如果是新创建的论文，初始化 Elasticsearch 索引
        PaperDocument.init()  # 确保索引已经创建
    # 更新或创建 Elasticsearch 中的文档
    doc = PaperDocument(meta={'id': instance.paper_id})
    doc.update(instance)


# 删除时同步删除 Elasticsearch 中的文档
@csrf_exempt
@receiver(post_delete, sender=Paper)
def delete_paper_from_elasticsearch(sender, instance, **kwargs):
    """
    论文数据删除时，从 Elasticsearch 中删除相应的文档。
    """
    PaperDocument(meta={'id': instance.paper_id}).delete()


@csrf_exempt
def search_paper(request):
    query = "P"  # 设置查询字符串为 "M"，模拟搜索过程

    # 使用 Redis 缓存的键来存储查询结果
    cache_key = f"paper_search_{query}"

    # 先检查缓存中是否有查询结果
    cached_results = cache.get(cache_key)
    if cached_results:
        print("Cache hit! Returning results from cache.")
        return JsonResponse({"results": cached_results}, status=200)

    # 使用 Elasticsearch 搜索 Paper 文档
    search = Search(index="papers").query("multi_match", query=query,
                                          fields=["title"])

    # 执行搜索
    response = search.execute()

    # 如果没有找到任何结果，返回提示
    if not response.hits:
        print("No papers found for query:", query)
        return JsonResponse({"message": "No papers found for the query."}, status=404)

    # 打印查询的结果（仅用于调试）
    print(f"Search results for '{query}':")
    for hit in response:
        print(f"Title: {hit.title}, Abstract: {hit.abstract}")

    # 构建返回结果
    results = [{
        "paper_id": hit.paper_id,
        "title": hit.title,
        "authorships": hit.authorships,
        "institutions": hit.institutions,
        "publish_date": hit.publish_date,
        "journal": hit.journal,
        "volume": hit.volume,
        "issue": hit.issue,
        "doi": hit.doi,
        "favorites": hit.favorites,
        "abstract": hit.abstract,
        "keywords": hit.keywords,
        "citation_count": hit.citation_count,
        "download_link": hit.download_link,
        "original_link": hit.original_link,
        "references": hit.references_works,
        "research_fields": hit.research_fields,
        "status": hit.status,
        "created_time": hit.created_time,
        "remarks": hit.remarks
    } for hit in response]

    # 将查询结果存储到 Redis 缓存中，缓存时间设置为 1 小时（3600秒）
    cache.set(cache_key, results, timeout=3600)

    return JsonResponse({"results": results}, status=200)


# @csrf_exempt
# def get_article(request):
#     '''
#     1. 检查缓存（cache.get）：如果缓存命中（即有数据），直接返回缓存的数据；
#         一旦查询到文章数据，将其存入 Redis 缓存中，缓存时间为 1 小时（3600 秒）。以后相同的查询可以直接从缓存中获取。
#     2. 使用 Django ORM 来查询数据库获取文章数据
#     '''
#     if request.method == 'GET':
#         # 从 GET 请求的参数中获取文章 ID

#         article_id = request.GET.get('id')
#         if not article_id:
#             return JsonResponse({"error": "Missing 'id' parameter"}, status=400)

#         # 使用 Redis 缓存的键来存储文章数据:使用论文 ID (article_id) 作为缓存键的组成部分
#         cache_key = f"article_{article_id}"

#         # 先检查缓存中是否有文章数据
#         cached_article = cache.get(cache_key)
#         # if cached_article:
#         #     print("Cache hit! Returning article data from cache.")
#         #     return JsonResponse({"article": cached_article}, status=200)

#         try:

#             # 使用 Elasticsearch 查询获取论文数据
#             # paper = Search(index="papers").query('match', paper_id=article_id).execute()
#             # if not paper.hits:
#             #     return JsonResponse({"error": "Paper not found"}, status=404)
#             # paper = paper[0]

#             # 使用 Django ORM 查询
#             # 获取论文数据
#             paper = Paper.objects.filter(paper_id=article_id).first()
#             # 如果没有找到文章，返回 404 错误
#             if not paper:
#                 return JsonResponse({"error": "Paper not found"}, status=404)

#             scholarAuthor = [{"id": user.user_id, "name": user.username} for user in
#                              paper.uploaded_by.all()]

#             # 构造返回的 JSON 数据
#             # 获取 users 列表（通过 uploaded_by 关联查询）
#             users = [{"id": user.user_id, "name": user.username} for user in
#                      paper.uploaded_by.all()]
#             article_data = {
#                 "title": paper.title,
#                 "author": transform_to_author_format(paper.authorships),
#                 "users": users,
#                 "institution": extract_display_names(paper.institutions),
#                 "year": str(paper.publish_date.year),
#                 "DOI": paper.doi,
#                 "abstract": process_abstract_to_string(paper.abstract),
#                 "journal": {
#                     "name": paper.journal,
#                     "volume": paper.volume,
#                     "issue": paper.issue,
#                 },

#                 "citation": [],  # 目前没有具体的引用数据，可以填充
#                 "citedCnt": paper.citation_count,
#                 "starCnt": paper.favorites,
#                 "cmtCnt": 0,  # 假设评论数为 0
#                 "fields": transform_to_field_format(paper.research_fields),
#                 "relation": [],  # 相关文献可以在这里填充
#                 "scholarAuthor": scholarAuthor,
#                 "download": paper.download_link,
#             }

#             # 将查询结果存储到 Redis 缓存中，缓存时间设置为 1 小时（3600秒）
#             cache.set(cache_key, article_data, timeout=3600)

#             return JsonResponse({"article": article_data}, status=200)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
#     else:
#         return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


# def process_abstract_to_string(abstract):
#     # 如果是非字符串或 "null"，返回空
#     if not abstract or (isinstance(abstract, str) and abstract.lower() == "null"):
#         return ""
#     # 若已是字符串，尝试判断是否是 JSON 格式的词频分布，如果是则重建原文本
#     if isinstance(abstract, str):
#         s = abstract.strip()
#         if s.startswith("{") and s.endswith("}"):
#             try:
#                 import json
#                 data = json.loads(abstract)
#                 word_positions = []
#                 for word, positions in data.items():
#                     for pos in positions:
#                         word_positions.append((pos, word))
#                 word_positions.sort(key=lambda x: x[0])
#                 return " ".join([w for _, w in word_positions])
#             except:
#                 return abstract
#         return abstract
#     return ""

# 初始化 Elasticsearch 客户端
es_client = Elasticsearch(
    hosts=["http://localhost:9200"],
    http_auth=("elastic", "123456")
)


def extract_display_names(institutions):
    # 假设这个函数提取机构的 display_name
    if not isinstance(institutions, list):
        return []
    return [institution.get("display_name", "") for institution in institutions if "display_name" in institution]


def process_abstract_to_string(abstract_raw):
    """处理 abstract 字段，将其转换为字符串"""
    if isinstance(abstract_raw, dict):
        word_positions = []
        for word, positions in abstract_raw.items():
            for pos in positions:
                if isinstance(pos, int):
                    word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join([w for _, w in word_positions])
    elif isinstance(abstract_raw, str):
        return abstract_raw
    return ""


def transform_to_author_format(authorships):
    """将 authorships 转换为前端需要的格式"""
    return [{"id": author.get("id", ""), "authorName": author.get("display_name", "")} for author in authorships]


def extract_display_names(institutions):
    """提取 institutions 的 display_name 字段"""
    return [inst.get("display_name", "") for inst in institutions]


def transform_to_field_format(research_fields):
    """将 research_fields 转换为前端需要的格式"""
    return [{"id": field.get("id", ""), "name": field.get("display_name", "")} for field in research_fields]


# @csrf_exempt
# def get_article(request):
#     if request.method == 'GET':
#         article_id = request.GET.get('id')
#         if not article_id:
#             return JsonResponse({"error": "Missing 'id' parameter"}, status=400)

#         try:
#             # 使用 Elasticsearch 查询
#             result = es_client.search(
#                 index='papers_index',
#                 body={
#                     "_source": "*",
#                     "query": {
#                         "term": {
#                             "paper_id": article_id
#                         }
#                     }
#                 }
#             )

#             # 检查是否有匹配文档
#             if not result['hits']['hits']:
#                 return JsonResponse({"error": "Paper not found"}, status=404)

#             hit = result['hits']['hits'][0]['_source']

#             # 处理 abstract
#             abstract_raw = hit.get("abstract", "")
#             abstract = process_abstract_to_string(abstract_raw)

#             # 处理 publish_date
#             publish_date_raw = hit.get("publish_date")
#             if isinstance(publish_date_raw, str):
#                 year = publish_date_raw.split(
#                     "-")[0] if publish_date_raw else ""
#             else:
#                 year = ""

#             # 确保 authorships、institutions、research_fields 均为 list
#             authorships = hit.get("authorships", [])
#             if not isinstance(authorships, list):
#                 authorships = []
#             institutions = hit.get("institutions", [])
#             if not isinstance(institutions, list):
#                 institutions = []
#             research_fields = hit.get("research_fields", [])
#             if not isinstance(research_fields, list):
#                 research_fields = []

#             article_data = {
#                 "title": hit.get("title", ""),
#                 "author": transform_to_author_format(authorships),
#                 "users": [],  # ES 中无 uploaded_by
#                 "institution": extract_display_names(institutions),
#                 "year": year,
#                 "DOI": hit.get("doi", ""),
#                 "abstract": abstract,
#                 "journal": {
#                     "name": hit.get("journal", ""),
#                     "volume": hit.get("volume", ""),
#                     "issue": hit.get("issue", ""),
#                 },
#                 "citation": [],
#                 "citedCnt": hit.get("citation_count", 0),
#                 "starCnt": hit.get("favorites", 0),
#                 "cmtCnt": 0,
#                 "fields": transform_to_field_format(research_fields),
#                 "relation": [],
#                 "scholarAuthor": [],  # ES 中无 uploaded_by
#                 "download": hit.get("download_link", ""),
#             }

#             return JsonResponse({"article": article_data}, status=200)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
#     else:
#         return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

@csrf_exempt
def get_article(request):
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

    try:
        article_id = request.GET.get('id')
        if not article_id:
            return JsonResponse({"error": "Missing 'id' parameter"}, status=400)
        
        # 使用 Elasticsearch 查询 openalex_paper_id.keyword
        result = es_client.search(
            index='papers_index_v2',  # 使用最新的索引
            body={
                "_source": "*",
                "query": {
                    "term": {
                        "openalex_paper_id.keyword": article_id  # 精确匹配
                    }
                }
            }
        )

        # 检查是否有匹配文档
        if not result['hits']['hits']:
            return JsonResponse({"error": "Paper not found"}, status=404)

        hit = result['hits']['hits'][0]['_source']

        # 处理 abstract
        abstract_raw = hit.get("abstract", "")
        abstract = process_abstract_to_string(abstract_raw)
        print(abstract_raw)

        # 处理 publish_date
        publish_date_raw = hit.get("publish_date")
        print("publish_date_raw" + publish_date_raw)
        if isinstance(publish_date_raw, str):
            try:
                # 尝试解析完整的日期时间格式
                publish_date = datetime.strptime(publish_date_raw, "%Y-%m-%dT%H:%M:%S")
                year = publish_date.year
            except ValueError:
                try:
                    # 尝试解析仅日期部分
                    publish_date = datetime.strptime(publish_date_raw, "%Y-%m-%d")
                    year = publish_date.year
                except ValueError:
                    print("ValueError出现，year值为空")
                    year = ""
        else:
            print("isinstance错误，year值为空")
            year = ""

        # 确保 authorships、institutions、research_fields 均为 list
        authorships = hit.get("authorships", [])
        if not isinstance(authorships, list):
            authorships = []
        institutions = hit.get("institutions", [])
        if not isinstance(institutions, list):
            institutions = []
        research_fields = hit.get("research_fields", [])
        if not isinstance(research_fields, list):
            research_fields = []

        # 参考文献
        references_works=hit.get("references_works", [])
        references_info=[]
        for reference_openalex_id in references_works:
            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            # 精确匹配
                            "openalex_paper_id.keyword": reference_openalex_id  
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            title=[]
            authors_name=[]

            if result['hits']['hits']:
                hit = result['hits']['hits'][0]['_source']
                title=hit.get("title","")
                reference_authorships=hit.get("authorships","")
                authors_name=[author['display_name'] for author in reference_authorships]

            references_info.append({
                "authors":authors_name,
                "articleId":reference_openalex_id,
                "articleTitle":title
            })

        # 相关文献
        related_works=hit.get("related_works", [])
        related_info=[]
        for related_openalex_id in related_works:
            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            # 精确匹配
                            "openalex_paper_id.keyword": related_openalex_id  
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            title=[]
            authors_name=[]

            if result['hits']['hits']:
                hit = result['hits']['hits'][0]['_source']
                title=hit.get("title","")
                related_authorships=hit.get("authorships","")
                authors_name=[author['display_name'] for author in related_authorships]

            related_info.append({
                "authors":authors_name,
                "articleId":related_openalex_id,
                "articleTitle":title
            })
        
        article_data = {
            "title": hit.get("title", ""),
            "author": transform_to_author_format(authorships),
            "users": [],  # ES 中无 uploaded_by
            "institution": extract_display_names(institutions),
            "year": year,
            "DOI": hit.get("doi", ""),
            "abstract": abstract,
            "journal": {
                "name": hit.get("journal", ""),
                "volume": hit.get("volume", ""),
                "issue": hit.get("issue", ""),
            },
            "reference":references_info,
            "citation": [],  # 根据需要填充
            "citedCnt": hit.get("citation_count", 0),
            "starCnt": hit.get("favorites", 0),
            "cmtCnt": 0,  # 根据需要填充
            "fields": transform_to_field_format(research_fields),
            "relation": related_info,  # 根据需要填充
            "scholarAuthor": [],  # ES 中无 uploaded_by
            "download": hit.get("download_link", ""),
        }

        return JsonResponse({"article": article_data}, status=200)

    except es_exceptions.ConnectionError:
        return JsonResponse({"error": "Failed to connect to Elasticsearch"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# def get_top_papers(request):
    
#     if request.method == 'GET':
#         # 使用 Redis 缓存的键来存储前 10 个收藏数最高的论文数据
#         cache_key = "top_favorite_papers"

#         # 先检查缓存中是否有前 10 个论文数据
#         cached_top_papers = cache.get(cache_key)
#         if cached_top_papers:
#             print("Cache hit! Returning top papers from cache.")
#             return JsonResponse({"articles": cached_top_papers}, status=200)

#         try:
#             # 查询收藏数前十的论文
#             # top_papers = Paper.objects.all().order_by('-favorites')[:10]

#             # 构造返回的 JSON 数据
#             # articles = []
#             # for paper in top_papers:
#             #     # 获取 authors 列表（直接从论文的 authors 属性中获取）
#             #     authors = [{"userName": author['display_name'], "userId": author['id']}
#             #                for author in paper.authorships]
#             #     articles.append({
#             #         "authors": authors,
#             #         "paperId": paper.openalex_paper_id,
#             #         "paperTitle": paper.title,
#             #         "year": str(paper.publish_date.year) if paper.publish_date else "N/A",
#             #         "abstract": process_abstract_to_string(paper.abstract),
#             #         "collectNum": paper.favorites,
#             #         "citationNum": paper.citation_count,
#             #     })
#             # 使用 Elasticsearch 查询收藏数前十的论文
#             print("wobeidiaoyongl ")
#             search = Search(index='papers_index_v2') \
#                 .sort('-favorites') \
#                 .filter('exists', field='favorites') \
#                 .extra(size=10)

#             response = search.execute()

#             articles = []
#             for hit in response:
#                 authors = [{"userName": author['display_name'],
#                             "userId": author['id']} for author in hit.authorships]
                
#                 publish_date = hit.publish_date
#                 if isinstance(publish_date, str):
#                     try:
#                         publish_date = datetime.strptime(
#                             publish_date, "%Y-%m-%d")
#                     except ValueError:
#                         publish_date = None

#                 articles.append({
#                     "authors": authors,
#                     "paperId": hit.openalex_paper_id,
#                     "paperTitle": hit.title,
#                     "year": str(hit.publish_date.year) if hit.publish_date else "N/A",
#                     "abstract": hit.abstract or "",
#                     "collectNum": hit.favorites,
#                     "citationNum": hit.citation_count,
#                 })
#             # 将查询结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
#             cache.set(cache_key, articles, timeout=3600)

#             return JsonResponse({"articles": articles}, status=200)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

#     else:
#         return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def get_top_papers(request):
    if request.method == 'GET':
        # # 使用 Redis 缓存的键来存储前 10 个收藏数最高的论文数据
        # cache_key = "top_favorite_papers"

        # # 先检查缓存中是否有前 10 个论文数据
        # cached_top_papers = cache.get(cache_key)
        # if cached_top_papers:
        #     print("Cache hit! Returning top papers from cache.")
        #     return JsonResponse({"articles": cached_top_papers}, status=200)

        try:
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "match_all": {}
                    },
                    "sort": [
                        {
                            "favorites": {
                                "order": "desc"
                            }
                        }
                    ],
                    "size": 10
                }
            )

            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"error": "Paper not found"}, status=404)



            # # 使用 Elasticsearch 查询收藏数前十的论文
            # search = Search(index='papers_index_v2') \
            #     .sort('-favorites') \
            #     .extra(size=10)

            # response = search.execute()

            articles = []
            # for hit in response:
            for hit in result['hits']['hits']:
                # hit_dict = hit.to_dict()
                hit_dict = hit['_source']

                # 处理 authorships
                authorships = hit_dict.get('authorships', [])
                authors = []
                for author in authorships:
                    authors.append({
                        "userName": author.get('display_name', ""),
                        "userId": author.get('id', "")
                    })

                # 处理 publish_date
                publish_date_str = hit_dict.get('publish_date', "")
                publish_date = None
                if isinstance(publish_date_str, str):
                    try:
                        # 尝试解析完整的日期时间格式
                        publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        try:
                            # 尝试解析仅日期部分
                            publish_date = datetime.strptime(publish_date_str, "%Y-%m-%d")
                        except ValueError:
                            publish_date = None

                year = str(publish_date.year) if isinstance(publish_date, datetime) else "N/A"

                # paper = Paper.objects.get(openalex_paper_id = hit_dict.get('openalex_paper_id', ""))

                # 构建文章数据
                articles.append({
                    "authors": authors,
                    "paperId": hit_dict.get('openalex_paper_id', ""),
                    "paperTitle": hit_dict.get('title', ""),
                    "year": year,
                    "abstract": hit_dict.get('abstract', "") or "",
                    "collectNum": hit_dict.get('favorites', 0),
                    # "collectNum": paper.favorites,
                    "citationNum": hit_dict.get('citation_count', 0),
                })

            # # 将查询结果存储到 Redis 缓存中，缓存时间设置为 1 小时（3600秒）
            # cache.set(cache_key, articles, timeout=3600)

            return JsonResponse({"articles": articles}, status=200, safe=False)

        except Paper.DoesNotExist:
            return JsonResponse({"error": "Paper not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

# @csrf_exempt
# def get_recommended_papers(request):
#     if request.method == 'GET':

#         # 使用 Redis 缓存的键来存储前 10 个引用数最高的论文数据
#         cache_key = "top_referred_papers"

#         # 先检查缓存中是否有前 10 个论文数据
#         cached_top_papers = cache.get(cache_key)
#         if cached_top_papers:
#             print("Cache hit! Returning top papers from cache.")
#             return JsonResponse({"articles": cached_top_papers}, status=200)

#         try:
#             # 查询引用数前十的论文
#             # top_papers = Paper.objects.all().order_by('-citation_count')[:10]
#             # # 构造返回的 JSON 数据
#             # articles = []
#             # for paper in top_papers:
#             #     # 获取 authors 列表（直接从论文的 authors 属性中获取）
#             #     authors = [{"userName": author['display_name'], "userId": author['id']}
#             #                for author in paper.authorships]
#             #     articles.append({
#             #         "authors": authors,
#             #         "paperId": paper.openalex_paper_id,
#             #         "paperTitle": paper.title,
#             #         "year": str(paper.publish_date.year) if paper.publish_date else "N/A",
#             #         "abstract": process_abstract_to_string(paper.abstract),
#             #         "collectNum": paper.favorites,
#             #         "citationNum": paper.citation_count,
#             #     })
#             # 使用 Elasticsearch 查询引用数前十的论文
#             search = Search(index='papers_index_v2') \
#                 .sort('-citation_count') \
#                 .filter('exists', field='citation_count') \
#                 .extra(size=10)

#             response = search.execute()

#             articles = []
#             for hit in response:
#                 authors = [{"userName": author['display_name'],
#                             "userId": author['id']} for author in hit.authorships]

#                 articles.append({
#                     "authors": authors,
#                     "paperId": hit.openalex_paper_id,
#                     "paperTitle": hit.title,
#                     "year": str(hit.publish_date.year) if hit.publish_date else "N/A",
#                     "abstract": hit.abstract or "",
#                     "collectNum": hit.favorites,
#                     "citationNum": hit.citation_count,
#                 })
#             # 将查询结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
#             cache.set(cache_key, articles, timeout=3600)

#             return JsonResponse({"articles": articles}, status=200)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

#     else:
#         return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

@csrf_exempt
def get_recommended_papers(request):
    if request.method == 'GET':

        # 使用 Redis 缓存的键来存储前 10 个引用数最高的论文数据
        cache_key = "top_referred_papers"

        # 先检查缓存中是否有前 10 个论文数据
        cached_top_papers = cache.get(cache_key)
        if cached_top_papers:
            print("Cache hit! Returning top papers from cache.")
            return JsonResponse({"articles": cached_top_papers}, status=200, safe=False)

        try:
            # 使用 Elasticsearch 查询引用数前十的论文
            search = Search(index='papers_index_v2') \
                .sort('-citation_count') \
                .extra(size=10)

            response = search.execute()

            articles = []
            for hit in response:
                hit_dict = hit.to_dict()

                # 处理 authorships
                authorships = hit_dict.get('authorships', [])
                authors = []
                for author in authorships:
                    authors.append({
                        "userName": author.get('display_name', ""),
                        "userId": author.get('id', "")
                    })

                # 处理 publish_date
                publish_date_str = hit_dict.get('publish_date', "")
                publish_date = None
                if isinstance(publish_date_str, str):
                    try:
                        # 尝试解析完整的日期时间格式
                        publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        try:
                            # 尝试解析仅日期部分
                            publish_date = datetime.strptime(publish_date_str, "%Y-%m-%d")
                        except ValueError:
                            publish_date = None
                elif isinstance(publish_date_str, datetime):
                    publish_date = publish_date_str

                year = str(publish_date.year) if isinstance(publish_date, datetime) else "N/A"

                # 构建文章数据
                articles.append({
                    "authors": authors,
                    "paperId": hit_dict.get('openalex_paper_id', ""),
                    "paperTitle": hit_dict.get('title', ""),
                    "year": year,
                    "abstract": hit_dict.get('abstract', "") or "",
                    "collectNum": hit_dict.get('favorites', 0),
                    "citationNum": hit_dict.get('citation_count', 0),
                })
            # 将查询结果存储到 Redis 缓存中，缓存时间设置为 1 小时（3600秒）
            cache.set(cache_key, articles, timeout=3600)

            return JsonResponse({"articles": articles}, status=200, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

@csrf_exempt
def get_statistics(request):
    """
    获取总体统计数据
    """
    if request.method == 'GET':
        # 尝试从 Redis 获取缓存的统计数据
        cache_key = "statistics_data"
        cached_statistics = cache.get(cache_key)

        if cached_statistics:
            # 如果缓存中存在数据，直接返回缓存的数据
            print("Cache hit! Returning statistics from cache.")
            return JsonResponse(cached_statistics, status=200)
        try:
            # 作者总数
            author_count = User.objects.count()

            # 机构总数（排除空机构，统计唯一机构）
            organizations_count = (
                User.objects.exclude(institution="")
                .values_list('institution', flat=True)
                .distinct()
                .count()
            )
            print("111")
            # for paper in Paper.objects.exclude(research_fields=None):
            #     print(paper.research_fields)
            # 研究领域总数（取每篇论文的所有研究领域，去重统计）
            research_fields = set(
                field['id']
                for paper in Paper.objects.exclude(research_fields=None)
                if paper.research_fields  # 确保 research_fields 不是 None 或空列表
                for field in paper.research_fields  # 遍历每篇论文的研究领域
            )
            fields_count = len(research_fields)
            print("222")
            # 期刊总数（排除空期刊，统计唯一期刊）
            journal_count = (
                Paper.objects.exclude(journal=None)
                .values_list('journal', flat=True)
                .distinct()
                .count()
            )
            # 论文总数
            paper_count = Paper.objects.count()
            # 格式化返回结果
            statistics = {
                "authorCount": f"{author_count:,}",
                "organizationsCount": f"{organizations_count:,}",
                "fieldsCount": f"{fields_count:,}",
                "journalCount": f"{journal_count:,}",
                "paperCount": f"{paper_count:,}"
            }
            # 将统计数据存入 Redis 缓存，设置缓存过期时间为 10 分钟 (600秒)
            cache.set(cache_key, statistics, timeout=600)
            return JsonResponse(statistics, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def search_papers_by_name(request):
    """
    按作者名搜索论文 (GET + Body 参数)
    """
    if request.method == 'GET':
        try:
            # 从请求体中解析 JSON 数据
            body = json.loads(request.body)
            name = body.get('name', '').strip()

            if not name:
                return JsonResponse({"error": "作者名不能为空"}, status=400)

            # 尝试从 Redis 获取缓存的结果
            cache_key = f"search_papers_by_name:{name}"
            cached_results = cache.get(cache_key)

            if cached_results:
                # 如果缓存存在，直接返回缓存的数据
                print("Cache hit! Returning papers from cache.")
                return JsonResponse(cached_results, safe=False, status=200)

            # 查询包含指定作者名的论文
            papers = Paper.objects.filter(authorships__icontains=name)

            # 构造返回数据
            results = []
            for paper in papers:
                results.append({
                    "title": paper.title,
                    "date": paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else "未知",
                    "journal": paper.journal if paper.journal else "未知",
                    # 保留作者字段为字符串形式
                    "authors": extract_display_names(paper.authorships),
                })

            # 将查询结果存入 Redis，设置缓存过期时间为 1 小时
            cache.set(cache_key, results, timeout=3600)

            return JsonResponse(results, safe=False, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "无效的 JSON 格式"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)


@csrf_exempt
def simple_search_papers(request):
    search_key = request.GET.get('searchKey', '').strip()
    user_id = request.GET.get('userid')

    # 缓存键基于 search_key 和 user_id 生成
    cache_key = f"search_papers:{search_key}:{user_id}" if user_id else f"search_papers:{search_key}"

    # 先尝试从 Redis 缓存中获取数据
    cached_result = cache.get(cache_key)
    if cached_result:
        # 如果缓存存在，直接返回缓存的结果
        print("Cache hit! Returning papers from cache.")
        return JsonResponse(cached_result, safe=False)

    # 获取用户对象（如果提供 userId）
    user = None
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    # 搜索论文（标题、关键词、摘要中任意一个字段匹配即可）
    papers = Paper.objects.filter(
        Q(title__icontains=search_key) |
        Q(keywords__icontains=search_key) |
        Q(abstract__icontains=search_key)
    ) if search_key else Paper.objects.all()

    # 构造响应数据
    result = []
    for paper in papers:
        # 判断是否为用户收藏的论文
        is_favorite = user.favorite_papers.filter(
            pk=paper.pk).exists() if user else False

        # 构造 authors 列表
        authors = []
        if paper.authorships and paper.institutions:
            # 保证两个列表一一对应
            for author, institution in zip(extract_display_names(paper.authorships),
                                           extract_display_names(paper.institutions)):
                authors.append(
                    {"authorName": author, "institution": institution})

        # 构造 users 列表
        users = []
        # 获取 users 列表（通过 uploaded_by 关联查询）
        users = [{"id": user.user_id, "name": user.username, "workspace": user.institution} for user in
                 paper.uploaded_by.all()]

        # 构造每篇论文的响应
        result.append({
            "Id": paper.paper_id,
            "isFavorate": is_favorite,
            "title": paper.title,
            "date": paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else "",
            "journal": paper.journal or "",
            "citations": paper.citation_count,
            "authors": authors,
            "keywords": paper.keywords or [],
            "users": users
        })
    # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
    cache.set(cache_key, result, timeout=3600)

    return JsonResponse(result, safe=False)


# @csrf_exempt
# def advanced_search_papers(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         user_id = data.get('userId', None)
#         page = data.get('page', 1)
#         sort = data.get('sort', 1)
#         filter_data = data.get('filter', {})
#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 构建缓存 key
#         cache_key = f"advanced_search:{user_id}:{str(search_conditions)}:{str(date_range)}"

#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning papers from cache.")
#             return JsonResponse(cached_result, safe=False)

#         # 构建搜索查询
#         query = Q()
#         for index, condition in enumerate(search_conditions):
#             value = condition.get('value', '').strip()
#             logic = condition.get('logic', 'and').lower()
#             scope = condition.get('scope', '').lower()

#             if not value:
#                 continue

#             if not scope:  # 如果 scope 为空，同时从 'title', 'author', 'keyword' 中查找
#                 sub_query = Q(title__icontains=value) | Q(
#                     authorships__icontains=value) | Q(keywords__icontains=value)
#             else:
#                 # 根据 scope 设置搜索字段
#                 field = {
#                     'title': 'title__icontains',
#                     'author': 'authorships__icontains',
#                     'keyword': 'keywords__icontains'
#                 }.get(scope)

#                 if not field:
#                     continue
#                 sub_query = Q(**{field: value})
#             if index == 0 and not logic:
#                 logic = 'and'
#             # 根据 logic 处理逻辑操作符
#             if logic == 'and':
#                 query &= sub_query
#             elif logic == 'or':
#                 query |= sub_query
#             elif logic == 'not':
#                 query &= ~sub_query

#         # 处理 filter_data 进行进一步过滤
#         keys = filter_data.get('keys', [])
#         years = filter_data.get('years', [])
#         author_organizations = filter_data.get('authorOrganizations', [])

#         if keys:
#             query &= Q(keywords__in=keys)

#         if years:
#             try:
#                 years = [int(year) for year in years]
#                 query &= Q(publish_date__year__in=years)
#             except ValueError:
#                 return JsonResponse({'error': 'Invalid year format. Years should be integers.'}, status=400)

#         if author_organizations:
#             query &= Q(authorships__institution__in=author_organizations)

#         # 获取日期范围，检查其格式（可为空）
#         if date_range:
#             if len(date_range) == 2:
#                 try:
#                     start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
#                     end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
#                     query &= Q(publish_date__gte=start_date,
#                                publish_date__lte=end_date)
#                 except ValueError:
#                     return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
#             else:
#                 return JsonResponse({'error': 'Invalid date range format. Provide start and end date.'}, status=400)
#         # 如果 date_range 是空数组，直接跳过日期过滤，忽略日期范围

#         # 执行查询
#         papers = Paper.objects.filter(query)
#         if not papers.exists():
#             return JsonResponse([], safe=False)
#         # 构造响应数据
#         # 根据 sort 参数排序
#         sort_field = 'publish_date'  # 默认排序
#         sort_order = ''

#         if sort == 1:  # 匹配度排序
#             papers = papers.annotate(
#                 match_count=Count(
#                     Case(
#                         When(title__icontains=value, then=1),
#                         When(authorships__icontains=value, then=1),
#                         When(keywords__icontains=value, then=1),
#                         output_field=IntegerField(),
#                     )
#                 )
#             ).order_by('-match_count')
#         elif sort == 2:  # 时间排序
#             sort_field = 'publish_date'
#         elif sort == 3:  # 被引量排序
#             sort_field = 'citation_count'

#         if sort == -1 or sort == -2 or sort == -3:
#             sort_order = '-' + sort_field
#         else:
#             sort_order = sort_field

#         if sort != 1:
#             papers = papers.order_by(sort_order)

#         # 分页
#         paginator = Paginator(papers, 10)  # 每页10条
#         try:
#             papers_page = paginator.page(page)
#         except PageNotAnInteger:
#             papers_page = paginator.page(1)
#         except EmptyPage:
#             papers_page = paginator.page(paginator.num_pages)

#         # 构造响应数据

#         result = []
#         for paper in papers_page:
#             # 判断是否为用户收藏的论文
#             is_favorite = user.favorite_papers.filter(
#                 pk=paper.pk).exists() if user else False

#             # 构造 authors 列表
#             authors = []
#             if paper.authorships and paper.institutions:
#                 # 保证两个列表一一对应
#                 # for author, institution in zip(extract_display_names(paper.authorships),
#                 #                                extract_display_names(paper.institutions)):
#                 #     authors.append(
#                 #
#                 #         {"userName": author, "authorOrganization": institution, "id": paper.authorships.id})
#                 for author, institution in zip_longest(paper.authorships, paper.institutions,
#                                                        fillvalue={"display_name": ""}):
#                     authors.append({
#                         "userName": author["display_name"],
#                         # 如果没有对应的机构，使用空字符串
#                         "authorOrganization": institution["display_name"],
#                         "id": author["id"]
#                     })
#             # 构造 users 列表
#             users = [{"id": user.user_id, "name": user.username, "workspace": user.institution} for user in
#                      paper.uploaded_by.all()]

#             # 构造每篇论文的响应
#             result.append({
#                 "Id": paper.paper_id,
#                 "isFavorate": is_favorite,
#                 "title": paper.title,
#                 "date": paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else "",
#                 "journal": paper.journal or "",
#                 "citations": paper.citation_count,
#                 "authors": authors,
#                 "keywords": paper.keywords or [],
#                 "users": users,
#                 "download": paper.download_link
#             })

#         # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
#         cache.set(cache_key, result, timeout=3600)

#         return JsonResponse(result, safe=False)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# 初始化 Elasticsearch 客户端
es_client = Elasticsearch(
    hosts=[{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
    http_auth=('elastic', '123456')  # 替换为您的用户名和密码
)




# @csrf_exempt
# def advanced_search_papers(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         user_id = data.get('userId', None)
#         page = data.get('page', 1)
#         sort = data.get('sort', 1)
#         filter_data = data.get('filter', {})

#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#                 print("current User: ", user)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 构建缓存 key，包含 filter_data
#         cache_key = f"advanced_search:{user_id}:{page}:{str(search_conditions)}:{str(date_range)}:{str(filter_data)}"

#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning papers from cache.")
#             return JsonResponse(cached_result, safe=False)

#         # 处理 search_conditions
#         must_queries = []
#         for condition in search_conditions:
#             logic = condition.get('logic')
#             value = condition.get('value')
#             scope = condition.get('scope')

#             # 检查并处理逻辑运算符
#             if logic and isinstance(logic, str):
#                 logic = logic.strip().upper()
#             else:
#                 logic = None  # 或者设置为默认逻辑，如 'AND'

#             # 检查并处理值
#             if value and isinstance(value, str):
#                 value = value.strip()
#             else:
#                 value = None  # 或者跳过此条件

#             # 检查并处理范围
#             if scope and isinstance(scope, str):
#                 scope = scope.strip()
#             else:
#                 scope = None  # 或者设置为默认范围

#             if value and scope:
#                 # 根据具体的查询需求构建查询
#                 must_queries.append({
#                     "match": {
#                         scope: value
#                     }
#                 })

#         # 处理日期范围
#         if len(date_range) == 2:
#             start_date, end_date = date_range
#             if start_date and isinstance(start_date, str):
#                 start_date = start_date.strip()
#             else:
#                 start_date = None

#             if end_date and isinstance(end_date, str):
#                 end_date = end_date.strip()
#             else:
#                 end_date = None

#             if start_date or end_date:
#                 must_queries.append({
#                     "range": {
#                         "publish_date": {
#                             "gte": start_date if start_date else "1900-01-01",
#                             "lte": end_date if end_date else "2100-12-31"
#                         }
#                     }
#                 })

#         # 处理 filter_data
#         filter_clauses = []
#         keys = filter_data.get('keys', [])
#         years = filter_data.get('years', [])
#         author_orgs = filter_data.get('authorOrganizations', [])

#         if keys:
#             filter_clauses.append({
#                 "terms": {
#                     "keywords.keyword": keys
#                 }
#             })

#         if years:
#             should_year_ranges = []
#             for year in years:
#                 try:
#                     year_int = int(year)
#                     should_year_ranges.append({
#                         "range": {
#                             "publish_date": {
#                                 "gte": f"{year}-01-01T00:00:00",
#                                 "lte": f"{year}-12-31T23:59:59"
#                             }
#                         }
#                     })
#                 except ValueError:
#                     continue

#             if should_year_ranges:
#                 filter_clauses.append({
#                     "bool": {
#                         "should": should_year_ranges,
#                         "minimum_should_match": 1
#                     }
#                 })

#         if author_orgs:
#             filter_clauses.append({
#                 "terms": {
#                     "institutions.display_name.keyword": author_orgs
#                 }
#             })

#         # 组合 Bool 查询
#         es_query = {
#             "bool": {
#                 "must": must_queries + filter_clauses
#             }
#         }

#         # 构建 Elasticsearch 查询体
#         es_query_body = {
#             "query": es_query,
#             "from": (page - 1) * 10,
#             "size": 10
#         }

#         # 添加排序
#         if sort == 1:
#             es_query_body["sort"] = [{"favorites": {"order": "desc"}}]
#         elif sort == 2:
#             es_query_body["sort"] = [{"citation_count": {"order": "desc"}}]
#         # 根据需要添加其他排序选项

#         # 执行 Elasticsearch 查询
#         result = es_client.search(
#             index='papers_index_v2',
#             body=es_query_body
#         )

#         hits = result['hits']['hits']
#         total = result['hits']['total']['value']
#         # 获取用户收藏的论文 ID 集合，减少查询次数
#         favorite_paper_ids = set(user.favorite_papers.values_list(
#             'pk', flat=True)) if user else set()
#         articles = []
#         for hit in hits:

#             source = hit['_source']
#             abstract = process_abstract_to_string(source.get("abstract", ""))
#             paper_id = source.get("paper_id", "")
#             authorships = source.get("authorships", [])
#             if not isinstance(authorships, list):
#                 authorships = []
#             institutions = source.get("institutions", [])
#             if not isinstance(institutions, list):
#                 institutions = []
#             research_fields = source.get("research_fields", [])
#             if not isinstance(research_fields, list):
#                 research_fields = []
#             authors = []
#             is_favorite = int(paper_id) in favorite_paper_ids if str(
#                 paper_id).isdigit() else False
#             if authorships and institutions:
#                 # 保证两个列表一一对应
#                 for author, institution in zip_longest(authorships, institutions, fillvalue={"display_name": "", "id": ""}):
#                     authors.append({
#                         "authorName": author.get("display_name", ""),
#                         "authorOrganization": institution.get("display_name", ""),
#                         "authorId": author.get("id", "")
#                     })

#             publish_date_str = source.get("publish_date", "")
#             publish_date = None
#             if isinstance(publish_date_str, str):
#                 try:
#                     publish_date = datetime.strptime(
#                         publish_date_str, "%Y-%m-%dT%H:%M:%S")
#                 except ValueError:
#                     try:
#                         publish_date = datetime.strptime(
#                             publish_date_str, "%Y-%m-%d")
#                     except ValueError:
#                         publish_date = None

#             articles.append({
#                 "Id": source.get("openalex_paper_id", ""),
#                 "isFavorate": is_favorite,
#                 "title": source.get("title", ""),
#                 "authors": authorships,
#                 "institution": extract_display_names(institutions),
#                 "date": publish_date.strftime('%Y-%m-%d') if publish_date else "N/A",
#                 "DOI": source.get("doi", ""),
#                 "abstract": abstract,
#                 "journal": source.get("journal", ""),
#                 "citations": source.get("citation_count", 0),
#                 "keywords": source.get("keywords", []),
#                 "download": source.get("download_link", ""),
#             })

#         response_data = {
#             "total": total,
#             "page": page,
#             "articles": articles
#         }

#         # 将结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
#         cache.set(cache_key, response_data, timeout=7200)

#         return JsonResponse(response_data, status=200, safe=False)

#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
#     except es_exceptions.ConnectionError:
#         return JsonResponse({'error': 'Failed to connect to Elasticsearch'}, status=500)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# @csrf_exempt
# def advanced_search_papers(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         user_id = data.get('userId', None)
#         page = data.get('page', 1)
#         sort = data.get('sort', 1)
#         filter_data = data.get('filter', {})

#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#                 print("current User: ", user)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 将 sort 也纳入缓存 key，以避免多次查询时因缓存导致排序不变
#         cache_key = f"advanced_search:{user_id}:{page}:{sort}:{str(search_conditions)}:{str(date_range)}:{str(filter_data)}"

#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result is not None:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning papers from cache.")
#             return JsonResponse(cached_result, safe=False)

#         # 处理 search_conditions
#         must_queries = []
#         for condition in search_conditions:
#             logic = condition.get('logic')
#             value = condition.get('value')
#             scope = condition.get('scope')

#             # 处理逻辑运算符
#             if logic and isinstance(logic, str):
#                 logic = logic.strip().upper()
#             else:
#                 logic = None  # 默认逻辑

#             # 处理查询值
#             if value and isinstance(value, str):
#                 value = value.strip()
#             else:
#                 value = None

#             # 处理scope
#             if scope and isinstance(scope, str):
#                 scope = scope.strip()
#             else:
#                 scope = None

#             # 简单构建match查询
#             if value and scope:
#                 must_queries.append({
#                     "match": {
#                         scope: value
#                     }
#                 })

#         # 处理日期范围
#         if len(date_range) == 2:
#             start_date, end_date = date_range
#             if start_date and isinstance(start_date, str):
#                 start_date = start_date.strip()
#             else:
#                 start_date = None

#             if end_date and isinstance(end_date, str):
#                 end_date = end_date.strip()
#             else:
#                 end_date = None

#             if start_date or end_date:
#                 must_queries.append({
#                     "range": {
#                         "publish_date": {
#                             "gte": start_date if start_date else "1900-01-01",
#                             "lte": end_date if end_date else "2100-12-31"
#                         }
#                     }
#                 })

#         # 处理 filter_data
#         filter_clauses = []
#         keys = filter_data.get('keys', [])
#         years = filter_data.get('years', [])
#         author_orgs = filter_data.get('authorOrganizations', [])

#         if keys:
#             filter_clauses.append({
#                 "terms": {
#                     "keywords.keyword": keys
#                 }
#             })

#         if years:
#             should_year_ranges = []
#             for year in years:
#                 try:
#                     year_int = int(year)
#                     should_year_ranges.append({
#                         "range": {
#                             "publish_date": {
#                                 "gte": f"{year}-01-01T00:00:00",
#                                 "lte": f"{year}-12-31T23:59:59"
#                             }
#                         }
#                     })
#                 except ValueError:
#                     continue
#             if should_year_ranges:
#                 filter_clauses.append({
#                     "bool": {
#                         "should": should_year_ranges,
#                         "minimum_should_match": 1
#                     }
#                 })

#         if author_orgs:
#             filter_clauses.append({
#                 "terms": {
#                     "institutions.display_name.keyword": author_orgs
#                 }
#             })

#         # 组合 Bool 查询
#         es_query = {
#             "bool": {
#                 "must": must_queries + filter_clauses
#             }
#         }

#         # 构建 Elasticsearch 查询体
#         es_query_body = {
#             "query": es_query,
#             "from": (page - 1) * 10,
#             "size": 10
#         }

#         # 添加排序逻辑
#         # sort == 1, 根据搜索相似度（_score）降序;  sort == -1, 相似度升序
#         # sort == 2, 引用量降序;                sort == -2, 引用量升序
#         # sort == 3, 时间降序;                  sort == -3, 时间升序
#         if sort == 1:
#             es_query_body["sort"] = [{"_score": {"order": "desc"}}]
#         elif sort == -1:
#             es_query_body["sort"] = [{"_score": {"order": "asc"}}]
#         elif sort == 2:
#             es_query_body["sort"] = [{"citation_count": {"order": "desc"}}]
#         elif sort == -2:
#             es_query_body["sort"] = [{"citation_count": {"order": "asc"}}]
#         elif sort == 3:
#             es_query_body["sort"] = [{"publish_date": {"order": "desc"}}]
#         elif sort == -3:
#             es_query_body["sort"] = [{"publish_date": {"order": "asc"}}]

#         # 执行 Elasticsearch 搜索
#         result = es_client.search(
#             index='papers_index_v2',
#             body=es_query_body
#         )

#         hits = result['hits']['hits']
#         total = result['hits']['total']['value']

#         # 获取用户收藏的论文 ID 集合
#         favorite_paper_ids = set(user.favorite_papers.values_list('pk', flat=True)) if user else set()

#         articles = []
#         for hit in hits:
#             source = hit['_source']
#             abstract = process_abstract_to_string(source.get("abstract", ""))
#             paper_id = source.get("paper_id", "")
#             authorships = source.get("authorships", [])
#             if not isinstance(authorships, list):
#                 authorships = []
#             institutions = source.get("institutions", [])
#             if not isinstance(institutions, list):
#                 institutions = []
#             research_fields = source.get("research_fields", [])
#             if not isinstance(research_fields, list):
#                 research_fields = []

#             is_favorite = str(paper_id).isdigit() and int(paper_id) in favorite_paper_ids

#             # 拼装作者信息
#             authors = []
#             if authorships and institutions:
#                 for author, institution in zip_longest(authorships, institutions, fillvalue={"display_name": "", "id": ""}):
#                     authors.append({
#                         "authorName": author.get("display_name", ""),
#                         "authorOrganization": institution.get("display_name", ""),
#                         "authorId": author.get("id", "")
#                     })

#             publish_date_str = source.get("publish_date", "")
#             publish_date = None
#             if isinstance(publish_date_str, str):
#                 try:
#                     publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S")
#                 except ValueError:
#                     try:
#                         publish_date = datetime.strptime(publish_date_str, "%Y-%m-%d")
#                     except ValueError:
#                         publish_date = None

#             articles.append({
#                 "Id": source.get("openalex_paper_id", ""),
#                 "isFavorate": is_favorite,
#                 "title": source.get("title", ""),
#                 "authors": authorships,
#                 "institution": extract_display_names(institutions),
#                 "date": publish_date.strftime('%Y-%m-%d') if publish_date else "N/A",
#                 "DOI": source.get("doi", ""),
#                 "abstract": abstract,
#                 "journal": source.get("journal", ""),
#                 "citations": source.get("citation_count", 0),
#                 "keywords": source.get("keywords", []),
#                 "download": source.get("download_link", ""),
#             })

#         response_data = {
#             "total": total,
#             "page": page,
#             "articles": articles
#         }

#         # 将结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
#         cache.set(cache_key, response_data, timeout=7200)

#         return JsonResponse(response_data, status=200, safe=False)

#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
#     except es_exceptions.ConnectionError:
#         return JsonResponse({'error': 'Failed to connect to Elasticsearch'}, status=500)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def advanced_search_papers(request):
    # 处理 search_conditions
    must_queries = []
    should_queries = []
    must_not_queries = []
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

    try:
        data = json.loads(request.body)  # 从请求体中获取 JSON 数据
        search_conditions = data.get('searchConditions', [])
        date_range = data.get('dateRange', [])
        user_id = data.get('userId', None)
        page = data.get('page', 1)
        sort = data.get('sort', 1)
        filter_data = data.get('filter', {})

        # 检查 user_id 是否存在，并验证用户
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                print("current User: ", user)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)
        else:
            user = None  # 如果 user_id 为 None，确保 user 被定义
        if not isinstance(search_conditions, list) or not isinstance(date_range, list):
            return JsonResponse({'error': 'Invalid input format.'}, status=400)

        # 将 sort 也纳入缓存 key，以避免多次查询时因缓存导致排序不变
        cache_key = f"advanced_search:{user_id}:{page}:{sort}:{str(search_conditions)}:{str(date_range)}:{str(filter_data)}"

        # 尝试从 Redis 获取缓存数据
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            # 如果缓存存在，直接返回缓存的结果
            print("Cache hit! Returning papers from cache.")
            return JsonResponse(cached_result, safe=False)

        # 处理 search_conditions
        must_queries = []
        tmplogic = 'AND'
        if len(search_conditions) > 1:
            tmplogic = search_conditions[1].get('logic').strip().upper()
        for condition in search_conditions:
            logic = condition.get('logic')
            value = condition.get('value')
            scope = condition.get('scope')

            # 处理逻辑运算符
            if logic and isinstance(logic, str):
                logic = logic.strip().upper()
            else:
                logic = None  # 默认逻辑
            if not logic:
                logic = tmplogic
            # 处理查询值
            if value and isinstance(value, str):
                value = value.strip()
            else:
                value = None

            # 处理scope
            if scope and isinstance(scope, str):
                scope = scope.strip()
            else:
                scope = None

            # 简单构建match查询
            if value and scope:
                query = {
                    "match": {
                        scope: value
                    }
                }
                if logic == "AND":
                    must_queries.append(query)
                elif logic == "OR":
                    should_queries.append(query)
                elif logic == "NOT":
                    must_not_queries.append(query)
                
        # 处理日期范围
        if len(date_range) == 2:
            start_date, end_date = date_range
            if start_date and isinstance(start_date, str):
                start_date = start_date.strip()
            else:
                start_date = None

            if end_date and isinstance(end_date, str):
                end_date = end_date.strip()
            else:
                end_date = None

            if start_date or end_date:
                must_queries.append({
                    "range": {
                        "publish_date": {
                            "gte": start_date if start_date else "1900-01-01",
                            "lte": end_date if end_date else "2100-12-31"
                        }
                    }
                })

        # 处理 filter_data
        filter_clauses = []
        keys = filter_data.get('keys', [])
        years = filter_data.get('years', [])
        author_orgs = filter_data.get('authorOrganizations', [])

        if keys:
            filter_clauses.append({
                "terms": {
                    "keywords.keyword": keys
                }
            })

        if years:
            should_year_ranges = []
            for year in years:
                try:
                    year_int = int(year)
                    should_year_ranges.append({
                        "range": {
                            "publish_date": {
                                "gte": f"{year}-01-01",  # 起始日期
                                "lte": f"{year}-12-31"   # 截止日期
                            }
                        }
                    })
                    
                except ValueError:
                    continue
            if should_year_ranges:
                filter_clauses.append({
                    "bool": {
                        "should": should_year_ranges,
                        "minimum_should_match": 1
                    }
                })

        if author_orgs:
            filter_clauses.append({
                "terms": {
                    "institutions.display_name.keyword": author_orgs
                }
            })

        # 组合 Bool 查询
        es_query = {
            "bool": {
                "must": must_queries + filter_clauses,
                "should": should_queries,  # OR 条件
                "must_not": must_not_queries  # NOT 条件
            }
        }

        # 构建 Elasticsearch 查询体
        es_query_body = {
            "query": es_query,
            "from": (page - 1) * 10,
            "size": 10
        }

        # 添加排序逻辑
        # sort == 1, 根据搜索相似度（_score）降序;  sort == -1, 相似度升序
        # sort == 2, 引用量降序;                sort == -2, 引用量升序
        # sort == 3, 时间降序;                  sort == -3, 时间升序
        if sort == 1:
            es_query_body["sort"] = [{"_score": {"order": "desc"}}]
        elif sort == -1:
            es_query_body["sort"] = [{"_score": {"order": "asc"}}]
        elif sort == 2:
            es_query_body["sort"] = [{"citation_count": {"order": "desc"}}]
        elif sort == -2:
            es_query_body["sort"] = [{"citation_count": {"order": "asc"}}]
        elif sort == 3:
            es_query_body["sort"] = [{"publish_date": {"order": "desc"}}]
        elif sort == -3:
            es_query_body["sort"] = [{"publish_date": {"order": "asc"}}]

        # 执行 Elasticsearch 搜索
        result = es_client.search(
            index='papers_index_v2',
            body=es_query_body
        )

        hits = result['hits']['hits']
        total = result['hits']['total']['value']
        query_time = result['took']  # 查询耗时（毫秒）
        # 获取用户收藏的论文 ID 集合
        favorite_paper_ids = set(user.favorite_papers.values_list('pk', flat=True)) if user else set()

        articles = []
        for hit in hits:
            source = hit['_source']
            abstract = process_abstract_to_string(source.get("abstract", ""))
            paper_id = source.get("paper_id", "")
            authorships = source.get("authorships", [])
            if not isinstance(authorships, list):
                authorships = []
            institutions = source.get("institutions", [])
            if not isinstance(institutions, list):
                institutions = []
            research_fields = source.get("research_fields", [])
            if not isinstance(research_fields, list):
                research_fields = []

            is_favorite = str(paper_id).isdigit() and int(paper_id) in favorite_paper_ids

            # 拼装作者信息
            authors = []
            if authorships and institutions:
                for author, institution in zip_longest(authorships, institutions, fillvalue={"display_name": "", "id": ""}):
                    authors.append({
                        "authorName": author.get("display_name", ""),
                        "authorOrganization": institution.get("display_name", ""),
                        "authorId": author.get("id", "")
                    })

            publish_date_str = source.get("publish_date", "")
            publish_date = None
            if isinstance(publish_date_str, str):
                try:
                    publish_date = datetime.strptime(publish_date_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    try:
                        publish_date = datetime.strptime(publish_date_str, "%Y-%m-%d")
                    except ValueError:
                        publish_date = None

            articles.append({
                "Id": source.get("openalex_paper_id", ""),
                "isFavorite": is_favorite,
                "title": source.get("title", ""),
                "authors": authorships,
                "institution": extract_display_names(institutions),
                "date": publish_date.strftime('%Y-%m-%d') if publish_date else "N/A",
                "DOI": source.get("doi", ""),
                "abstract": abstract,
                "journal": source.get("journal", ""),
                "citations": source.get("citation_count", 0),
                "keywords": source.get("keywords", []),
                "download": source.get("download_link", ""),
            })

        response_data = {
            "total": total,
            "page": page,
            "queryTime": query_time,  # 添加查询耗时到返回数据
            "articles": articles
        }

        # 将结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
        cache.set(cache_key, response_data, timeout=7200)

        return JsonResponse(response_data, status=200, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except es_exceptions.ConnectionError:
        return JsonResponse({'error': 'Failed to connect to Elasticsearch'})
    except Exception as e:
        return JsonResponse({'error': str(e)})

@csrf_exempt
def get_if_starPaper(request):
    if request.method == 'GET':
        try:
            user_id = request.GET.get('id')
            paper_id = request.GET.get('paperId')

            if not user_id or not paper_id:
                return JsonResponse({'status': 'Missing parameters'}, status=404)
            user = User.objects.get(user_id=user_id)
            if_favorite = user.favorite_papers.filter(
                openalex_paper_id=paper_id).exists()

            if if_favorite:
                return JsonResponse({'status': 'success', 'isStar': True})
            else:
                return JsonResponse({'status': 'success', 'isStar': False})

        except User.DoesNotExist:
            return JsonResponse({'status': 'User not found', 'isStar': False}, status=404)
        except Exception as e:
            return JsonResponse({'status': str(e), 'isStar': False}, status=500)


@csrf_exempt
def post_starPaper(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_id = body['id']
            openalex_paper_id = body['paperId']
            isStar = body['isStar']
            # 检查参数是否有效
            if not user_id or not openalex_paper_id or isStar is None:
                return JsonResponse({'message': 'Missing parameters'}, status=404)

            user = User.objects.get(user_id=user_id)


            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            "openalex_paper_id.keyword": openalex_paper_id  # 精确匹配
                        }
                    }
                }
            )

            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"message": "Paper not found"}, status=404)


            _id = result['hits']['hits'][0]['_id']
            hit = result['hits']['hits'][0]['_source']
            paper_id = hit.get("paper_id", 0)  # 获取paper_id - 主键
            paper = Paper.objects.get(paper_id=paper_id)
            favorites = paper.favorites
            
            
            # 需要收藏
            if isStar:
                # 如果还未收藏
                if not user.favorite_papers.filter(paper_id = paper_id).exists():
                    user.favorite_papers.add(paper)
                    favorites += 1
                    paper.favorites = favorites
                    paper.save()
                    # 使用 Elasticsearch 的 update API 更新 favorites 字段
                    response = es_client.update(
                        index="papers_index_v2",  # 索引名称
                        id=_id,  # es文档 ID
                        body={
                            "doc": {
                                "favorites": favorites  # 更新的字段和新值
                            }
                        }
                    )
                    # 返回成功消息
                    return JsonResponse({'message': 'success', 'response': str(response)})
                    
            # 取消收藏
            else:
                # 如果已收藏
                if user.favorite_papers.filter(paper_id = paper_id).exists():
                    favorites -= 1
                    paper.favorites = favorites
                    user.favorite_papers.remove(paper)
                    paper.save()
                    # 使用 Elasticsearch 的 update API 更新 favorites 字段
                    response = es_client.update(
                        index="papers_index_v2",  # 索引名称
                        id=_id,  # es文档 ID
                        body={
                            "doc": {
                                "favorites": favorites  # 更新的字段和新值
                            }
                        }
                    )
                    # 返回成功消息
                    return JsonResponse({'message': 'success', 'response': str(response)})
            
            # 返回成功消息
            return JsonResponse({'message': 'success'})

        except Paper.DoesNotExist:
            return JsonResponse({'message': 'Paper not found'}, status=404)
        except User.DoesNotExist:
            return JsonResponse({'message': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e), "test": {"_id": _id, "open": hit.get("openalex_paper_id", 0), "favorites": favorites}})


def generate_cache_key(key_data):
    # 将 dict 转换为 JSON 字符串adfgdfgas
    serialized_data = json.dumps(key_data, sort_keys=True)
    hashed_key = hashlib.md5(serialized_data.encode('utf-8')).hexdigest()
    return f"cache:{hashed_key}"


# @csrf_exempt
# def filter_data(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         user_id = data.get('userId', None)

#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 构建缓存 key
#         cache_key = generate_cache_key({
#             "type": "filter",
#             "user_id": user_id,
#             "search_conditions": search_conditions,
#             "date_range": date_range
#         })

#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning papers from cache.")
#             return JsonResponse(cached_result, safe=False)

#         # 构建搜索查询
#         query = Q()
#         for index, condition in enumerate(search_conditions):
#             value = condition.get('value', '').strip(
#             ) if condition.get('value') else ''
#             logic = condition.get('logic', 'and').lower(
#             ) if condition.get('logic') else 'and'
#             scope = condition.get('scope', '').lower(
#             ) if condition.get('scope') else ''

#             if not value:
#                 continue

#             if not scope:  # 如果 scope 为空，同时从 'title', 'author', 'keyword' 中查找
#                 sub_query = Q(title__icontains=value) | Q(
#                     authorships__icontains=value) | Q(keywords__icontains=value)
#             else:
#                 # 根据 scope 设置搜索字段
#                 field = {
#                     'title': 'title__icontains',
#                     'author': 'authorships__icontains',
#                     'keyword': 'keywords__icontains'
#                 }.get(scope)

#                 if not field:
#                     continue
#                 sub_query = Q(**{field: value})
#             if index == 0 and not logic:
#                 logic = 'and'
#             # 根据 logic 处理逻辑操作符
#             if logic == 'and':
#                 query &= sub_query
#             elif logic == 'or':
#                 query |= sub_query
#             elif logic == 'not':
#                 query &= ~sub_query

#         # 获取日期范围，检查其格式（可为空）
#         if date_range:
#             if len(date_range) == 2:
#                 try:
#                     start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
#                     end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
#                     query &= Q(publish_date__gte=start_date,
#                                publish_date__lte=end_date)
#                 except ValueError:
#                     return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
#             else:
#                 return JsonResponse({'error': 'Invalid date range format. Provide start and end date.'}, status=400)
#         # 如果 date_range 是空数组，直接跳过日期过滤，忽略日期范围

#         # 执行查询
#         papers = Paper.objects.filter(query)
#         if not papers.exists():
#             return JsonResponse([], safe=False)

#         # 构造响应数据
#         result = []
#         for paper in papers:
#             result.append({
#                 "Id": paper.paper_id,
#                 "title": paper.title,
#                 "date": paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else "",
#                 "journal": paper.journal or "",
#                 "citations": paper.citation_count,
#                 "authors": paper.authorships,
#                 "keywords": paper.keywords,
#                 "download": paper.download_link
#             })

#         # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
#         cache.set(cache_key, result, timeout=3600)

#         return JsonResponse(result, safe=False)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# 假设你已经导入了 User 和 Paper 模型以及 Redis 缓存


def generate_cache_key(key_data):
    # 将 dict 转换为 JSON 字符串并哈希处理
    serialized_data = json.dumps(key_data, sort_keys=True)
    hashed_key = hashlib.md5(serialized_data.encode('utf-8')).hexdigest()
    return f"cache:{hashed_key}"


@csrf_exempt
def filter_data(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

    try:
        data = json.loads(request.body)  # 从请求体中获取 JSON 数据
        search_conditions = data.get('searchConditions', [])
        date_range = data.get('dateRange', [])
        user_id = data.get('userId', None)

        # 检查 user_id 是否存在，并验证用户
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

        if not isinstance(search_conditions, list) or not isinstance(date_range, list):
            return JsonResponse({'error': 'Invalid input format.'}, status=400)

        # 构建缓存 key
        cache_key = generate_cache_key({
            "type": "filter",
            "user_id": user_id,
            "search_conditions": search_conditions,
            "date_range": date_range
        })

        # 尝试从 Redis 获取缓存数据
        cached_result = cache.get(cache_key)
        if cached_result:
            # 如果缓存存在，直接返回缓存的结果
            print("Cache hit! Returning keys and author organizations from cache.")
            return JsonResponse(cached_result, safe=False)

        # 初始化 Elasticsearch 客户端
        es = Elasticsearch(
            hosts=['http://localhost:9200'],
            basic_auth=('elastic', '123456'),  # 根据需要调整用户名和密码
            verify_certs=False  # 如果使用自签名证书，可能需要设置为 False
        )

        # 构建 Elasticsearch 查询
        must_clauses = []
        should_clauses = []
        must_not_clauses = []

        for index, condition in enumerate(search_conditions):
            value = condition.get('value', '').strip(
            ) if condition.get('value') else ''
            logic = condition.get('logic', 'and').lower(
            ) if condition.get('logic') else 'and'
            scope = condition.get('scope', '').lower(
            ) if condition.get('scope') else ''

            if not value:
                continue

            if not scope:
                clause = {
                    "bool": {
                        "should": [
                            {"match_phrase": {"title": value}},
                            {
                                "nested": {
                                    "path": "authorships",
                                    "query": {"match_phrase": {"authorships.display_name": value}}
                                }
                            },
                            {"match_phrase": {"keywords": value}}
                        ],
                        "minimum_should_match": 1
                    }
                }
            else:
                field = {
                    'title': 'title',
                    'author': 'authorships.display_name',
                    'keyword': 'keywords'
                }.get(scope)

                if not field:
                    continue

                if scope == 'author':
                    clause = {
                        "nested": {
                            "path": "authorships",
                            "query": {"match_phrase": {"authorships.display_name": value}}
                        }
                    }
                else:
                    clause = {"match_phrase": {field: value}}

            if logic == 'and':
                must_clauses.append(clause)
            elif logic == 'or':
                should_clauses.append(clause)
            elif logic == 'not':
                must_not_clauses.append(clause)

        # 处理日期范围
        if date_range and len(date_range) == 2:
            start_date_str, end_date_str = date_range
            if start_date_str and end_date_str:
                try:
                    start_date = datetime.strptime(
                        start_date_str, "%Y-%m-%d").isoformat()
                    end_date = datetime.strptime(
                        end_date_str, "%Y-%m-%d").isoformat()
                    date_clause = {
                        "range": {
                            "publish_date": {
                                "gte": start_date,
                                "lte": end_date
                            }
                        }
                    }
                    must_clauses.append(date_clause)
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # 组合 Bool 查询
        if not must_clauses and not should_clauses and not must_not_clauses:
            es_query = {"match_all": {}}
        else:
            es_query = {
                "bool": {
                    "must": must_clauses,
                    "should": should_clauses,
                    "must_not": must_not_clauses
                }
            }

        # 定义聚合，获取前20个关键词和作者单位
        aggs = {
            "top_keywords": {
                "terms": {"field": "keywords.keyword", "size": 20}
            },
            "top_author_org": {
                "nested": {
                    "path": "institutions"
                },
                "aggs": {
                    "top_author_orgs": {
                        "terms": {"field": "institutions.display_name.keyword", "size": 20}
                    }
                }
            }
        }

        # 记录发送到 Elasticsearch 的查询
        print(
            f"Elasticsearch query: {json.dumps({'query': es_query, 'aggs': aggs}, indent=2)}")

        # 执行 Elasticsearch 搜索
        response = es.search(
            index='papers_index_v2',  # 使用新的索引名称
            body={
                "query": es_query,
                "size": 0,  # 不返回具体文档，只需要聚合结果
                "aggs": aggs
            }
        )

        # 提取聚合结果
        try:
            top_20_keys = [bucket['key']
                           for bucket in response['aggregations']['top_keywords']['buckets']]
            top_20_author_org = [
                bucket['key'] for bucket in response['aggregations']['top_author_org']['top_author_orgs']['buckets']
            ]
        except KeyError as e:
            print(f"Aggregation key error: {str(e)}")
            return JsonResponse({'error': 'Aggregation structure error.'}, status=500)

        # 构造响应数据
        response_data = {
            "allKeys": top_20_keys,
            "allAuthorOrganization": top_20_author_org
        }

        # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
        cache.set(cache_key, response_data, timeout=3600)

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        print(f"Error in filter_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# @csrf_exempt
# def get_page(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         filter_data = data.get('filter', {})
#         user_id = data.get('userId', None)

#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 构建缓存 key
#         cache_key = generate_cache_key({
#             "type": "page",
#             "user_id": user_id,
#             "search_conditions": search_conditions,
#             "date_range": date_range
#         })
#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning papers from cache.")
#             return JsonResponse(cached_result, safe=False)

#         # 构建搜索查询
#         query = Q()
#         for index, condition in enumerate(search_conditions):
#             value = condition.get('value', '').strip(
#             ) if condition.get('value') else ''
#             logic = condition.get('logic', 'and').lower(
#             ) if condition.get('logic') else 'and'
#             scope = condition.get('scope', '').lower(
#             ) if condition.get('scope') else ''

#             if not value:
#                 continue

#             if not scope:  # 如果 scope 为空，同时从 'title', 'author', 'keyword' 中查找
#                 sub_query = Q(title__icontains=value) | Q(
#                     authorships__icontains=value) | Q(keywords__icontains=value)
#             else:
#                 # 根据 scope 设置搜索字段
#                 field = {
#                     'title': 'title__icontains',
#                     'author': 'authorships__icontains',
#                     'keyword': 'keywords__icontains'
#                 }.get(scope)

#                 if not field:
#                     continue
#                 sub_query = Q(**{field: value})
#             if index == 0 and not logic:
#                 logic = 'and'
#             # 根据 logic 处理逻辑操作符
#             if logic == 'and':
#                 query &= sub_query
#             elif logic == 'or':
#                 query |= sub_query
#             elif logic == 'not':
#                 query &= ~sub_query

#         # 获取日期范围，检查其格式（可为空）
#         if date_range:
#             if len(date_range) == 2:
#                 try:
#                     start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
#                     end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
#                     query &= Q(publish_date__gte=start_date,
#                                publish_date__lte=end_date)
#                 except ValueError:
#                     return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
#             else:
#                 return JsonResponse({'error': 'Invalid date range format. Provide start and end date.'}, status=400)
#         # 如果 date_range 是空数组，直接跳过日期过滤，忽略日期范围

#         # 执行查询
#         papers = Paper.objects.filter(query)
#         if not papers.exists():
#             return JsonResponse([], safe=False)
#         # 构造响应数据
#         result = []

#         # 获取 papers 的长度并除以 10
#         pages = (papers.count() + 9) // 10  # 向上取整，避免出现不完整的页数
#         result.append({
#             "page": pages
#         })

#         # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
#         cache.set(cache_key, result, timeout=3600)

#         return JsonResponse(result, safe=False)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# @csrf_exempt
# def get_page(request):
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

#     try:
#         data = json.loads(request.body)  # 从请求体中获取 JSON 数据
#         search_conditions = data.get('searchConditions', [])
#         date_range = data.get('dateRange', [])
#         filter_data = data.get('filter', {})
#         user_id = data.get('userId', None)

#         # 检查 user_id 是否存在，并验证用户
#         if user_id:
#             try:
#                 user = User.objects.get(pk=user_id)
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'User not found'}, status=404)

#         if not isinstance(search_conditions, list) or not isinstance(date_range, list):
#             return JsonResponse({'error': 'Invalid input format.'}, status=400)

#         # 构建缓存 key
#         cache_key = generate_cache_key({
#             "type": "page",
#             "user_id": user_id,
#             "search_conditions": search_conditions,
#             "date_range": date_range,
#             "filter": filter_data
#         })

#         # 尝试从 Redis 获取缓存数据
#         cached_result = cache.get(cache_key)
#         if cached_result is not None:
#             # 如果缓存存在，直接返回缓存的结果
#             print("Cache hit! Returning page count from cache.")
#             return JsonResponse({"page": cached_result}, safe=False)

#         # 初始化 Elasticsearch 客户端
#         es = Elasticsearch(
#             hosts=['http://localhost:9200'],
#             basic_auth=('elastic', '123456'),  # 根据需要调整用户名和密码
#             verify_certs=False  # 如果使用自签名证书，可能需要设置为 False
#         )

#         # 构建 Elasticsearch 查询
#         must_clauses = []
#         should_clauses = []
#         must_not_clauses = []

#         for index, condition in enumerate(search_conditions):
#             value = condition.get('value', '').strip(
#             ) if condition.get('value') else ''
#             logic = condition.get('logic', 'and').lower(
#             ) if condition.get('logic') else 'and'
#             scope = condition.get('scope', '').lower(
#             ) if condition.get('scope') else ''

#             if not value:
#                 continue  # 如果 value 为空，则忽略该条件

#             if not scope:  # 如果 scope 为空，同时从 'title', 'author', 'keyword' 中查找
#                 clause = {
#                     "bool": {
#                         "should": [
#                             {"match_phrase": {"title": value}},
#                             {
#                                 "nested": {
#                                     "path": "authorships",
#                                     "query": {
#                                         "match_phrase": {"authorships.display_name_keyword": value}
#                                     }
#                                 }
#                             },
#                             {"match_phrase": {"keywords.keyword": value}}
#                         ],
#                         "minimum_should_match": 1
#                     }
#                 }
#             else:
#                 # 根据 scope 设置搜索字段
#                 field = {
#                     'title': 'title.keyword',
#                     'author': 'authorships.display_name.keyword',
#                     'keyword': 'keywords.keyword'
#                 }.get(scope)

#                 if not field:
#                     continue  # 如果 scope 不在预期范围内，则忽略该条件

#                 if scope == 'author':
#                     clause = {
#                         "nested": {
#                             "path": "authorships",
#                             "query": {
#                                 "match_phrase": {"authorships.display_name_keyword": value}
#                             }
#                         }
#                     }
#                 else:
#                     clause = {"match_phrase": {field: value}}

#             if logic == 'and':
#                 must_clauses.append(clause)
#             elif logic == 'or':
#                 should_clauses.append(clause)
#             elif logic == 'not':
#                 must_not_clauses.append(clause)

#         # 处理日期范围
#         if date_range and len(date_range) == 2:
#             start_date_str, end_date_str = date_range
#             if start_date_str and end_date_str:
#                 try:
#                     # 验证日期格式
#                     start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#                     end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
#                     date_clause = {
#                         "range": {
#                             "publish_date": {
#                                 "gte": start_date.isoformat(),
#                                 "lte": end_date.isoformat()
#                             }
#                         }
#                     }
#                     must_clauses.append(date_clause)
#                 except ValueError:
#                     return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
#         elif date_range:
#             return JsonResponse({'error': 'Invalid date range format. Provide start and end date.'}, status=400)

#         # 处理 filter_data
#         # 例如 filter 中包含 "keys"、"years"、"authorOrganizations"
#         # 假设 "keys" 过滤 keywords, "years" 过滤 publish_date, "authorOrganizations" 过滤 institutions.display_name
#         filter_clauses = []

#         keys = filter_data.get('keys', [])
#         years = filter_data.get('years', [])
#         author_orgs = filter_data.get('authorOrganizations', [])

#         if keys:
#             # 确认 keys 对应的是 keywords，若 keys 实际应该对应其他字段，请调整
#             filter_clauses.append({
#                 "terms": {
#                     "keywords.keyword": keys  # 假设 keywords 已经有 .keyword 子字段
#                 }
#             })

#         if years:
#             # 使用 publish_date 的年份进行过滤
#             should_year_ranges = []
#             for year in years:
#                 try:
#                     year_int = int(year)
#                     should_year_ranges.append({
#                         "range": {
#                             "publish_date": {
#                                 "gte": f"{year}-01-01T00:00:00",
#                                 "lte": f"{year}-12-31T23:59:59"
#                             }
#                         }
#                     })
#                 except ValueError:
#                     continue  # 忽略无效的年份

#             if should_year_ranges:
#                 filter_clauses.append({
#                     "bool": {
#                         "should": should_year_ranges,
#                         "minimum_should_match": 1
#                     }
#                 })

#         if author_orgs:
#             filter_clauses.append({
#                 "terms": {
#                     "institutions.display_name.keyword": author_orgs  # 假设 display_name 有 .keyword 子字段
#                 }
#             })

#         # 组合 Bool 查询
#         es_query = {
#             "bool": {
#                 "must": must_clauses + filter_clauses,
#                 "should": should_clauses,
#                 "must_not": must_not_clauses
#             }
#         }

#         # 定义 Elasticsearch 查询体
#         query_body = {
#             "query": es_query,
#             "size": 0,  # 不需要返回具体文档，只需要总数
#             "track_total_hits": True  # 确保获取精确的 total hits
#         }

#         # 执行 Elasticsearch 搜索
#         response = es.search(
#             index='papers_index_v2',  # 使用重新构建的索引名称
#             body=query_body
#         )

#         # 获取总命中数
#         total_hits = response['hits']['total']['value']

#         # 计算页数（向上取整）
#         pages = ceil(total_hits / 10)

#         # 构造响应数据
#         response_data = pages

#         # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
#         cache.set(cache_key, response_data, timeout=3600)

#         return JsonResponse({"page": response_data}, safe=False)

#     except Exception as e:
#         print(f"Error in get_page: {str(e)}")
#         return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_page(request):
    # 处理 search_conditions
    must_queries = []
    should_queries = []
    must_not_queries = []
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

    try:
        data = json.loads(request.body)  # 从请求体中获取 JSON 数据
        search_conditions = data.get('searchConditions', [])
        date_range = data.get('dateRange', [])
        filter_data = data.get('filter', {})
        user_id = data.get('userId', None)

        # 检查 user_id 是否存在，并验证用户
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

        if not isinstance(search_conditions, list) or not isinstance(date_range, list):
            return JsonResponse({'error': 'Invalid input format.'}, status=400)

        # 构建缓存 key
        cache_key = generate_cache_key({
            "type": "page",
            "user_id": user_id,
            "search_conditions": search_conditions,
            "date_range": date_range,
            "filter": filter_data
        })

        # 尝试从 Redis 获取缓存数据
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            # 如果缓存存在，直接返回缓存的结果
            print("Cache hit! Returning page count from cache.")
            return JsonResponse({"page": cached_result}, safe=False)

        # 初始化 Elasticsearch 客户端
        es = Elasticsearch(
            hosts=['http://localhost:9200'],
            basic_auth=('elastic', '123456'),  # 根据需要调整用户名和密码
            verify_certs=False  # 如果使用自签名证书，可能需要设置为 False
        )

        # 构建 Elasticsearch 查询
        must_queries = []
        tmplogic = 'AND'
        if len(search_conditions) > 1:
            tmplogic = search_conditions[1].get('logic').strip().upper()
        for condition in search_conditions:
            logic = condition.get('logic')
            value = condition.get('value')
            scope = condition.get('scope')

            # 检查并处理逻辑运算符
            if logic and isinstance(logic, str):
                logic = logic.strip().upper()
            else:
                logic = None  # 或者设置为默认逻辑，如 'AND'
            
            if not logic:
                logic = tmplogic
            # 检查并处理值
            if value and isinstance(value, str):
                value = value.strip()
            else:
                value = None  # 或者跳过此条件

            # 检查并处理范围
            if scope and isinstance(scope, str):
                scope = scope.strip()
            else:
                scope = None  # 或者设置为默认范围

            if value and scope:
                query = {
                    "match": {
                        scope: value
                    }
                }
                if logic == "AND":
                    must_queries.append(query)
                elif logic == "OR":
                    should_queries.append(query)
                elif logic == "NOT":
                    must_not_queries.append(query)

        # 处理日期范围
        if len(date_range) == 2:
            start_date, end_date = date_range
            if start_date and isinstance(start_date, str):
                start_date = start_date.strip()
            else:
                start_date = None

            if end_date and isinstance(end_date, str):
                end_date = end_date.strip()
            else:
                end_date = None

            if start_date or end_date:
                must_queries.append({
                    "range": {
                        "publish_date": {
                            "gte": start_date if start_date else "1900-01-01",
                            "lte": end_date if end_date else "2100-12-31"
                        }
                    }
                })

        # 处理 filter_data
        filter_clauses = []
        keys = filter_data.get('keys', [])
        years = filter_data.get('years', [])
        author_orgs = filter_data.get('authorOrganizations', [])

        if keys:
            filter_clauses.append({
                "terms": {
                    "keywords.keyword": keys
                }
            })

        if years:
            should_year_ranges = []
            for year in years:
                try:
                    year_int = int(year)
                    should_year_ranges.append({
                        "range": {
                            "publish_date": {
                                "gte": f"{year}-01-01T00:00:00",
                                "lte": f"{year}-12-31T23:59:59"
                            }
                        }
                    })
                except ValueError:
                    continue

            if should_year_ranges:
                filter_clauses.append({
                    "bool": {
                        "should": should_year_ranges,
                        "minimum_should_match": 1
                    }
                })

        if author_orgs:
            filter_clauses.append({
                "terms": {
                    "institutions.display_name.keyword": author_orgs
                }
            })

        # 组合 Bool 查询
        # es_query = {
        #     "bool": {
        #         "must": must_queries + filter_clauses
        #     }
        # }
        es_query = {
            "bool": {
                "must": must_queries + filter_clauses,
                "should": should_queries,  # OR 条件
                "must_not": must_not_queries  # NOT 条件
            }
        }
        # 定义 Elasticsearch 查询体
        query_body = {
            "query": es_query,
            "size": 0,  # 不需要返回具体文档，只需要总数
            "track_total_hits": True  # 确保获取精确的 total hits
        }

        # 执行 Elasticsearch 搜索
        response = es.search(
            index='papers_index_v2',  # 使用重新构建的索引名称
            body=query_body
        )

        # 获取总命中数
        total_hits = response['hits']['total']['value']

        # 计算页数（向上取整）
        pages = ceil(total_hits / 10)

        # 构造响应数据
        response_data = pages

        # 将查询结果存入 Redis，并设置缓存过期时间为 1 小时（3600秒）
        cache.set(cache_key, response_data, timeout=3600)

        return JsonResponse({"page": response_data}, safe=False)

    except Exception as e:
        print(f"Error in get_page: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def hotest_organizations(request):
    try:
        if request.method == 'GET':
            organizations = Institution.objects.all().order_by(
                '-works_count')[:10]
            return_organizations = []
            for organization in organizations:
                return_organizations.append(
                    {'organizationName': organization.display_name, 
                     'works_number': organization.works_count,
                     'homepage': organization.homepage_url
                     })

            return JsonResponse({'organizations': return_organizations})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def hotest_fields(request):
    try:
        if request.method == 'GET':
            topic_result = es_client.search(
                index='topics_index_v1',  # 使用索引名称
                body={
                    "_source": ["openalex_topic_id", "display_name", "works_count"],  # 只返回需要的字段
                    "query": {
                        "match_all": {}  # 不过滤，获取所有文档
                    },
                    "sort": [
                        {
                            "works_count": {  # 按照 'works_count' 排序
                                "order": "desc"  # 按降序排序
                            }
                        }
                    ],
                    "size": 10  # 只返回前 10 个结果
                }
            )

            fields = topic_result['hits']['hits'] #es 的返回数据

            if not fields:
                return JsonResponse({'error': 'Topics not found'}, status=404)
            
            return_message = []
            for field in fields:
                paper_result = es_client.search(
                    index='papers_index_v2',  # 使用索引名称
                    body={
                        "_source": ["paper_id", "openalex_paper_id"],  # 只返回需要的字段
                        "query": {
                            "nested": {
                                "path": "research_fields",
                                "query": {
                                    "term": {
                                        "research_fields.id.keyword": field['_source'].get('openalex_topic_id')
                                    }
                                }
                            }
                        },
                        "sort": [
                            {
                                "citation_count": {
                                    "order": "desc"  # 按降序排序
                                }
                            }
                        ],
                        "size": 1  # 只返回前 1 个结果
                    }
                )
                if not paper_result['hits']['hits']:
                    return_message.append({
                        'fieldName': field['_source'].get('display_name'),
                        'fieldId': field['_source'].get('openalex_topic_id'),
                        'works_number': field['_source'].get('works_count'),
                        'topArticleId': "",
                        'topArticleName': ""
                    })
                else:
                    return_message.append({
                        'fieldName': field['_source'].get('display_name'),
                        'fieldId': field['_source'].get('openalex_topic_id'),
                        'works_number': field['_source'].get('works_count'),
                        'topArticleId': paper_result['hits']['hits'][0]['_source'].get('openalex_paper_id'),
                        'topArticleName': paper_result['hits']['hits'][0]['_source'].get('title')
                    })
                # top_paper = Paper.objects.filter(research_fields__contains=[
                #     {"id": field.openalex_topic_id}]).order_by('-citation_count')[:1]

                # if top_paper:
                #     return_message.append({
                #         'fieldName': field.display_name,
                #         'works_number': field.works_count,
                #         'topArticleId': top_paper[0].paper_id,
                #         'topArticleName': top_paper[0].title
                #     })
                # else:
                #     return_message.append({
                #         'fieldName': field.display_name,
                #         'works_number': field.works_count,
                #         'topArticleId': "",
                #         'topArticleName': ""
                #     })

            return JsonResponse({'fields': return_message, "fff": fields})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def getStarCnt(request):
    if request.method == "GET":
        try:
            paper_openalex_id = request.GET.get('paperId')

            # 使用 Elasticsearch 查询 openalex_paper_id.keyword
            result = es_client.search(
                index='papers_index_v2',  # 使用最新的索引
                body={
                    "_source": "*",
                    "query": {
                        "term": {
                            "openalex_paper_id.keyword": paper_openalex_id  # 精确匹配
                        }
                    }
                }
            )
            # 检查是否有匹配文档
            if not result['hits']['hits']:
                return JsonResponse({"error": "Paper not found"}, status=404)
            hit = result['hits']['hits'][0]['_source']

            paper_id = hit.get('paper_id', 0)
            paper = Paper.objects.get(paper_id=paper_id)
            starcnt = hit.get('favorites', 0)

            return JsonResponse({"count": paper.favorites, "es_count": starcnt})
        
        except Paper.DoesNotExist:
            return JsonResponse({"error": "Paper not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)