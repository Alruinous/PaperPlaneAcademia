# Django 集成 Redis, Celery
## 1. 安装
### 1.1 Windows系统，本地安装
* 安装命令已加入`requirements.txt`

### 1.2 服务器安装
* `Ubuntu`系统安装`Redis`：
``` shell
sudo apt update
sudo apt install redis-server
```
* 启动`Redis`：
```shell
redis-server
```

* 查看`Redis`是否启动？
```shell
redis-cli
```

## 2. 配置Django设置
* 在`Django`的设置文件`settings.py`中，需要配置缓存和会话的后端为`Redis`。示例如下：
```python
# Redis的基本配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 配置Django缓存后端为Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        # 使用 Redis 的默认端口和数据库，例如：'redis://127.0.0.1:6379/1'
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',    
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 配置Django的会话后端为Redis（可选）
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# 配置 Celery（可选）
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Redis 作为任务队列
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # 任务结果存储
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
```

## 3. 使用Redis缓存数据
缓存键如下：
1. `paper_search_{query}`: 关键词`query`检索，缓存时间为 1 小时（3600 秒）
2. `article_{article_id}`: ID为`article_id`的论文检索，缓存时间为 1 小时（3600 秒）
3. `top_favorite_papers`: 前 10 个收藏数最高的论文数据，缓存时间设置为 2 小时（7200秒）
4. `top_referred_papers`: 前 10 个引用数最高的论文数据，缓存时间设置为 2 小时（7200秒）
5. `statistics_data`: 总体统计数据，缓存时间设置为 10 分钟（600秒）
6. `search_papers_by_name:{name}`: 包含指定作者名`name`的论文，缓存时间为 1 小时（3600 秒）
7. `search_papers:{search_key}:{user_id}` / `search_papers:{search_key}`: 缓存时间为 1 小时（3600 秒）
8. `advanced_search:{user_id}:{str(search_conditions)}:{str(date_range)}`: 缓存时间为 1 小时（3600 秒）
9. `starPaper:{user_id}:{paper_id}`: 指定用户是否收藏指定论文，缓存时间为 1 小时（3600 秒）



## 4. 使用Celery创建定时任务
### 4.1 编写Celery任务
* 在你的 Django 应用（例如 papers）下创建一个 tasks.py 文件，并定义更新缓存的任务。

### 4.2 设置定时任务
* 使用 Celery 的 beat 功能来定期执行任务，在 `your_project/celery.py` 中添加。

### 4.3 启动Celery 和 Celery Beat
* 前置条件：Redis 服务器正在运行。
* 启动 `Celery worker` 和 `Celery beat` 任务调度器。
启动 Celery worker：
```bash
celery -A your_project worker --loglevel=info
```
启动 Celery beat（定时任务调度器）：
```bash
celery -A your_project beat --loglevel=info
```

### 4.4 修改视图函数，优先从缓存获取数据
* 优先从 `Redis` 获取数据，如果缓存为空，则从数据库查询并返回。

### 4.5 定期更新缓存
* 例：通过 Celery 和 `beat` 定时任务，`update_top_papers_cache` 任务将每 2 小时重新计算 `top_ten_papers` 并将其缓存到 `Redis`。这样，视图会始终优先从缓存中获取数据，只有在缓存未命中时才会查询数据库。