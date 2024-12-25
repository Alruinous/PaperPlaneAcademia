import os
import json
import mysql.connector
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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

# 定义连接数据库的方法
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

# 插入数据到 Topic 表
def insert_into_topic(cursor, openalex_topic_id, display_name, works_count, cited_by_count, description, keywords, siblings):
    """
    将数据插入到 Topic 表中。
    :param cursor: 数据库游标
    :param openalex_topic_id: Topic 的 OpenAlex ID
    :param display_name: Topic 的显示名称
    :param works_count: 论文数量
    :param cited_by_count: 被引用次数
    :param description: Topic 描述
    :param keywords: 关键词 JSON 字符串
    :param siblings: 同级主题的 JSON 字符串
    """
    query = """
    INSERT INTO topics_topic (openalex_topic_id, display_name, works_count, cited_by_count, description, keywords, siblings)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (openalex_topic_id, display_name, works_count, cited_by_count, description, keywords, siblings))

# 删除 Topic 数据
def delete_topic_by_id(cursor, topic_id):
    """
    根据 Topic ID 删除数据
    :param cursor: 数据库游标
    :param topic_id: Topic 的 ID
    """
    query = "DELETE FROM topic WHERE topic_id = %s"
    cursor.execute(query, (topic_id,))

# 保存已处理的 JSON 文件路径到 processed_topics_json.txt
def save_processed_files(file_path, processed_files):
    """
    保存已处理的文件路径到 txt 文件
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for file in processed_files:
                f.write(file + '\n')
        print(f"已将已处理的文件路径保存到 {file_path}")
    except Exception as e:
        print(f"保存文件路径时发生错误: {e}")

# 读取已处理的 JSON 文件路径
def read_processed_files(file_path):
    """
    从文件中读取已处理的文件路径。如果文件不存在，创建文件并返回空集合。
    """
    processed_files = set()

    # 如果文件不存在，则创建一个新的文件
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 文件创建时为空
                pass
            print(f"{file_path} 文件不存在，已创建空文件。")
        except Exception as e:
            print(f"创建文件 {file_path} 时发生错误: {e}")
    else:
        try:
            # 如果文件存在，读取内容
            with open(file_path, 'r', encoding='utf-8') as f:
                processed_files = {line.strip() for line in f.readlines()}
        except Exception as e:
            print(f"读取已处理文件路径时发生错误: {e}")
    
    return processed_files

# 将已处理文件路径写入 processed_topics_json.txt
def write_processed_files(file_path, processed_files):
    """
    将已处理文件路径写入 processed_topics_json.txt 文件
    :param file_path: 文件路径
    :param processed_files: 已处理的文件路径集合
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(processed_files))

# 递归读取文件夹中的 JSON 文件并插入数据
def process_json_files_in_directory(directory, processed_files, processed_files_file, do_process=False):
    """
    递归读取目录下的所有 JSON 文件并插入数据到数据库。
    :param directory: 需要读取的文件夹路径
    :param processed_files: 用于记录已处理文件路径的集合
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_file_path = os.path.join(root, file)

                # 检查文件是否已处理过
                if json_file_path not in processed_files:
                    print(f"文件 {json_file_path} 被处理，跳过插入和删除操作。" if not do_process else f"文件 {json_file_path} 被处理，开始插入。")
                    processed_files.add(json_file_path)  # 标记为已处理

                    if do_process:
                        # 如果执行处理操作，调用插入函数
                        process_json_file(json_file_path)

                # 检查文件是否已处理过
                if json_file_path not in processed_files:
                    print(f"处理文件: {json_file_path}")
                    process_json_file(json_file_path)
                    processed_files.add(json_file_path)  # 标记为已处理
    
    # 更新 processed_authors_json.txt 文件
    write_processed_files(processed_files_file, processed_files)

# 处理单个 JSON 文件并插入数据
def process_json_file(json_file_path):
    """
    处理单个 JSON 文件，将数据插入数据库
    :param json_file_path: JSON 文件路径
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 打开 JSON 文件并按行读取
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if line:
                    try:
                        # 将每行当作单独的 JSON 对象解析
                        item = json.loads(line)

                        openalex_topic_id = item.get("id")
                        display_name = item.get("display_name")
                        works_count = item.get("works_count", 0)
                        cited_by_count = item.get("cited_by_count", 0)
                        description = item.get("description", "")
                        keywords = json.dumps(item.get("keywords", []))  # 转换为 JSON 字符串
                        siblings = json.dumps(item.get("siblings", []))  # 转换为 JSON 字符串

                        if openalex_topic_id and display_name:
                            insert_into_topic(cursor, openalex_topic_id, display_name, works_count, cited_by_count, description, keywords, siblings)

                    except json.JSONDecodeError as e:
                        print(f"文件 {json_file_path} 中的某一行解析失败，内容：{line[:100]}...\n错误：{e}")

        connection.commit()
        print(f"成功插入 {json_file_path} 中的数据到数据库。")
        
        # 删除已处理的文件
        os.remove(json_file_path)
        print(f"已删除文件: {json_file_path}")

    except Exception as e:
        connection.rollback()
        print(f"处理文件 {json_file_path} 时发生错误: {e}")

    finally:
        cursor.close()
        connection.close()

# 监听文件夹变化
class Watcher(FileSystemEventHandler):
    def __init__(self, directory, filepath, processed_file):
        self.directory = directory
        self.filepath = filepath
        self.processed_file = processed_file

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.json'):
            # 只处理新创建的文件，避免重复处理
            if event.src_path not in self.processed_file:
                print(f"新文件 {event.src_path} 被创建，开始处理。")
                process_json_file(event.src_path)
                self.processed_file.add(event.src_path)

                # 更新 processed_authors_json.txt
                save_processed_files(self.filepath, self.processed_file)

# 主程序入口
if __name__ == "__main__":
    # 设置要读取的工作目录
    works_directory = "/root/openalex-snapshot/data/topics" 
    processed_files_file = "/root/openalex-snapshot/data/processed_topics_json.txt"  # 存储已处理文件路径的文件
    
    # 读取已处理文件路径
    processed_files = read_processed_files(processed_files_file)

    # 初始时只遍历文件，记录已处理文件，不进行插入
    print("开始初始遍历文件...")
    process_json_files_in_directory(works_directory, processed_files, processed_files_file, do_process=False)

    # 初始遍历完成后开始插入和删除操作
    print("初始遍历完成，开始插入操作...")
    process_json_files_in_directory(works_directory, processed_files, processed_files_file, do_process=True)

    # 启动文件夹监控
    event_handler = Watcher(works_directory, processed_files_file, processed_files)  
    observer = Observer()
    observer.schedule(event_handler, works_directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
