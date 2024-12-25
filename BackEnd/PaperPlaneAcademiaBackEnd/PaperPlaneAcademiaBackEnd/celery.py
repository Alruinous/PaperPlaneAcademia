from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# 设置默认的 Django 配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PaperPlaneAcademiaBackEnd.settings')

app = Celery('PaperPlaneAcademiaBackEnd')

# 使用字符串告诉 Celery 使用哪个配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务模块
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-favorite-papers-every-2-hours': {
        'task': 'papers.tasks.update_favorite_papers_cache',  # 任务路径
        'schedule': crontab(minute=0, hour='*/2'),  # 每 2 小时执行一次
    },
    'update-referred-papers-every-2-hours': {
        'task': 'papers.tasks.update_referred_papers_cache',  # 任务路径
        'schedule': crontab(minute=0, hour='*/2'),  # 每 2 小时执行一次
    },
    'update-statistics-every-10-minutes': {
        'task': 'papers.tasks.update_statistics_cache',  # 任务路径
        'schedule': crontab(minute='*/10', hour=0),  # 每 10 分钟执行一次
    },
    'update-institution-scholars-every-6-hours': {
        'task': 'papers.tasks.update_institution_scholar_info',  # 任务路径
        'schedule': crontab(minute=0, hour='*/6'),  # 每 6 小时执行一次
    },
}