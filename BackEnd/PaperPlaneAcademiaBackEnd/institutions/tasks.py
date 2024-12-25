# claims/tasks.py

from celery import shared_task
from django.core.cache import cache
from papers.models import Paper
from users.models import User
from institutions.models import Institution
from authors.models import Author

@shared_task
def update_institution_scholar_info():
    try:
        # 获取所有机构（排除空机构）
        #institutions = Institution.objects.exclude(openalex_institution_id="").distinct()

        institution_dict = {}
        # 获取所有学者
        authors = Author.objects.all()

        # 遍历所有学者，处理他们的 last_known_institutions
        for author in authors:
            if author.last_known_institutions:
                # 遍历学者的所有机构
                for institution_info in author.last_known_institutions:
                    institution_id = institution_info.get("institution_id")
                    
                    # 如果机构ID存在，继续处理
                    if institution_id:
                        # 如果该机构ID尚未加入字典，则初始化它
                        if institution_id not in institution_dict:
                            institution_dict[institution_id] = []

                        # 将学者信息加入到该机构的字典列表中
                        institution_dict[institution_id].append({
                            "author_id": author.author_id,
                            "openalex_author_id": author.openalex_author_id,
                            "name": author.name
                        })

        # 将每个机构的字典数据存入 Redis 中，缓存时间为 6 小时
        for institution_id, scholars_data in institution_dict.items():
            redis_key = f"institution:{institution_id}"
            cache.set(redis_key, scholars_data, timeout=21600)  # 设置缓存，过期时间为6小时

        print("Institution scholar information cache updated successfully.")
    except Exception as e:
        print(f"Error updating institution scholar information cache: {e}")
