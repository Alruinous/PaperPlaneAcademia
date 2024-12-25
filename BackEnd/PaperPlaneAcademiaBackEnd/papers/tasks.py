# papers/tasks.py

from celery import shared_task
from django.core.cache import cache
from .models import Paper
from users.models import User

@shared_task
def update_favorite_papers_cache():
    try:
        # 查询收藏数前十的论文
        top_papers = Paper.objects.all().order_by('-favorites')[:10]

        # 构造返回的 JSON 数据
        articles = []
        for paper in top_papers:
            # 获取 authors 列表（直接从论文的 authors 属性中获取）
            authors = [{"userName": author_name} for author_name in paper.authors]

            # 获取 users 列表（通过 uploaded_by 关联查询）
            users = [{"userId": user.user_id, "userName": user.username} for user in paper.uploaded_by.all()]

            articles.append({
                "authors": authors,
                "paperId": str(paper.paper_id),
                "paperTitle": paper.title,
                "year": str(paper.publish_date.year) if paper.publish_date else "N/A",
                "abstract": paper.abstract,
                "collectNum": paper.favorites,
                "citationNum": paper.citation_count,
                "users": users
            })

        # 将查询结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
        cache.set('top_favorite_papers', articles, timeout=7200)  # 设置缓存
        print("Top favorite papers cache updated successfully.")
    except Exception as e:
        print(f"Error updating top papers cache: {e}")

@shared_task
def update_referred_papers_cache():
    try:
        # 查询引用数前十的论文
        top_papers = Paper.objects.all().order_by('-citation_count')[:10]

        # 构造返回的 JSON 数据
        articles = []
        for paper in top_papers:
            # 获取 authors 列表（直接从论文的 authors 属性中获取）
            authors = [{"userName": author_name} for author_name in paper.authors]

            # 获取 users 列表（通过 uploaded_by 关联查询）
            users = [{"userId": user.user_id, "userName": user.username} for user in paper.uploaded_by.all()]

            articles.append({
                "authors": authors,
                "paperId": str(paper.paper_id),
                "paperTitle": paper.title,
                "year": str(paper.publish_date.year) if paper.publish_date else "N/A",
                "abstract": paper.abstract,
                "collectNum": paper.favorites,
                "citationNum": paper.citation_count,
                "users": users
            })

        # 将查询结果存储到 Redis 缓存中，缓存时间设置为 2 小时（7200秒）
        cache.set('top_referred_papers', articles, timeout=7200)  # 设置缓存
        print("Top reffered papers cache updated successfully.")
    except Exception as e:
        print(f"Error updating top papers cache: {e}")

@shared_task
def update_statistics_cache():
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

        # 研究领域总数（取每篇论文的所有研究领域，去重统计）
        research_fields = set(
            field
            for paper in Paper.objects.exclude(research_fields=None)
            for field in paper.research_fields
        )
        fields_count = len(research_fields)

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
        cache.set('statistics_data', statistics, timeout=600)
        print("Top reffered papers cache updated successfully.")
    except Exception as e:
        print(f"Error updating statistics data cache: {e}")

