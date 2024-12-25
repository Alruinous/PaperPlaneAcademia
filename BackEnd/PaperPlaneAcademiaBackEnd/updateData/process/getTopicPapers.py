import mysql.connector
import json
import time

# 设置数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'paperbackenddb',  
        'USER': 'root',  
        'PASSWORD': '123456',  
        'HOST': '113.44.138.144',
        'PORT': '3306',
    }
}

# 获取数据库连接
def get_db_connection():
    """
    获取 MySQL 数据库连接
    """
    return mysql.connector.connect(
        host=DATABASES['default']['HOST'],
        user=DATABASES['default']['USER'],
        password=DATABASES['default']['PASSWORD'],
        database=DATABASES['default']['NAME'],
        port=DATABASES['default']['PORT']
    )

def update_topics_with_paper_info(papers):
    """
    批量更新论文对应的主题信息
    """
    try:
        # 连接到数据库
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 遍历所有传入的论文
        for paper in papers:
            # 获取当前论文的 research_fields (假设它是一个 JSON 字段)
            research_fields = json.loads(paper.get('research_fields', '[]'))

            if research_fields:
                for field in research_fields:
                    topic_id = field.get('id')
                    print(f"查找和更新主题 {topic_id} 的信息...")

                    # 查找 Topic 模型中是否已经存在该 research field
                    cursor.execute("SELECT * FROM topics_topic WHERE openalex_topic_id = %s", (topic_id,))
                    topic = cursor.fetchone()

                    # 强制清空当前查询结果，防止未读取的结果集
                    cursor.nextset()  # 这里用 nextset 清空任何可能存在的结果集

                    if topic:
                        print(f"更新主题 {topic_id} 对应的 topic_papers 字段...")

                        # 如果 Topic 存在，则更新 Topic 的 topic_papers 字段
                        topic_papers = json.loads(topic['topic_papers'] if topic['topic_papers'] else '[]')
                        topic_papers.append({
                            "paper_id": paper['paper_id'],
                            "openalex_paper_id": paper['openalex_paper_id'],
                            "title": paper['title'],
                        })

                        # 更新 topic_papers 字段
                        updated_topic_papers = json.dumps(topic_papers)
                        cursor.execute("""
                            UPDATE topics_topic
                            SET topic_papers = %s
                            WHERE openalex_topic_id = %s
                        """, (updated_topic_papers, topic_id))

        # 提交事务
        connection.commit()

        print(f"成功更新 {len(papers)} 篇论文的主题信息。")
    
    except Exception as e:
        print(f"批量处理论文时发生错误: {e}")
    
    finally:
        cursor.close()
        connection.close()

def process_all_papers():
    """
    处理所有现有论文
    """
    try:
        # 连接到数据库
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 查询所有论文
        cursor.execute("SELECT * FROM papers_paper")
        all_papers = cursor.fetchall()

        if all_papers:
            print(f"发现 {len(all_papers)} 条现有论文，开始批量更新...")

            # 强制清空任何未读取的查询结果
            cursor.nextset()

            update_topics_with_paper_info(all_papers)

        else:
            print("没有发现现有论文。")
    
    except Exception as e:
        print(f"处理现有论文时发生错误: {e}")
    
    finally:
        cursor.close()
        connection.close()

def monitor_new_papers():
    """
    监控 papers 表，从上次检查时间起，获取新增的论文，并批量更新主题信息。
    """
    last_checked_time = time.time()

    while True:
        try:
            # 连接到数据库
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # 查询自上次检查以来新增的论文，批量获取（如一次获取 100 条）
            cursor.execute("""
                SELECT * FROM papers_paper
                WHERE created_time > FROM_UNIXTIME(%s)
                ORDER BY created_time ASC
                LIMIT 100
            """, (last_checked_time,))
            new_papers = cursor.fetchall()

            # 强制清空任何未读取的查询结果
            cursor.nextset()

            if new_papers:
                print(f"发现 {len(new_papers)} 条新论文，开始批量更新...")

                update_topics_with_paper_info(new_papers)

                # 更新检查时间
                last_checked_time = time.time()

            # 休眠一定时间后再次检查（例如 10 秒）
            time.sleep(10)

        except Exception as e:
            print(f"监控过程中发生错误: {e}")
        
        finally:
            cursor.close()
            connection.close()

# 先处理所有现有论文，然后进入监控新论文阶段
process_all_papers()  # 处理所有现有论文
monitor_new_papers()  # 进入监控新论文的模式
