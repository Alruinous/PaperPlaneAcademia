from __future__ import absolute_import, unicode_literals

# 为了确保在 Django 启动时加载 Celery
from .celery import app as celery_app

__all__ = ('celery_app',)