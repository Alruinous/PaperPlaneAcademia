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

# 数据库插入操作
def insert_into_author_table(cursor, author_id, orcid, display_name, display_name_alternatives_json, works_count,
                             cited_by_count, two_year_mean_citedness, h_index, two_year_cited_by_count,
                             institutions_json, topics_json):
    """
    将作者信息插入数据库
    """
    insert_query = """
    INSERT INTO authors_author (openalex_author_id, orcid, name, name_alternatives, works_count, cited_by_count,
                         two_yr_mean_citedness, h_index, two_yr_cited_by_count, last_known_institutions, topics)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        # 插入数据
        cursor.execute(insert_query, (author_id, orcid, display_name, display_name_alternatives_json, works_count, cited_by_count,
                                      two_year_mean_citedness, h_index, two_year_cited_by_count, institutions_json, topics_json))
    except Exception as e:
        print(f"插入数据时发生错误: {e}")
        print(f"机构信息: {institutions_json}")
        print(f"话题信息: {topics_json}")

# 保存已处理的 JSON 文件路径到 processed_authors_json.txt
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

# 将已处理文件路径写入 processed_authors_json.txt
def write_processed_files(file_path, processed_files):
    """
    将已处理文件路径写入 processed_authors_json.txt 文件
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
                # 去除每行的前后空白符和换行符
                line = line.strip()

                # 只处理非空行
                if line:
                    try:
                        # 将每行当作单独的 JSON 对象解析
                        item = json.loads(line)

                        openalex_author_id = item.get("id")
                        orcid = item.get("orcid", "")
                        if orcid is None:
                            orcid=""
                        display_name = item.get("display_name")
                        display_name_alternatives = item.get("display_name_alternatives", [])
                        display_name_alternatives_json = json.dumps(display_name_alternatives) if display_name_alternatives else None
                        works_count = item.get("works_count")
                        cited_by_count = item.get("cited_by_count")

                        # 统计数据
                        summary_stats = item.get("summary_stats", {})
                        two_year_mean_citedness = summary_stats.get("2yr_mean_citedness", "")
                        h_index = summary_stats.get("h_index", "")
                        two_year_cited_by_count = summary_stats.get("2yr_cited_by_count", "")
                        
                        # 最近的机构信息
                        last_known_institutions = item.get("last_known_institutions", [])
                        institutions_info = []
                        
                        for institution in last_known_institutions:
                            if "id" in institution and "display_name" in institution and "country_code" in institution:
                                institution_info = {
                                    "institution_id": institution['id'],
                                    "display_name": institution['display_name'],
                                    "country_code": institution['country_code']
                                }
                                institutions_info.append(institution_info)
                        institutions_json = json.dumps(institutions_info) if institutions_info else None
                        
                        # 话题贡献信息
                        topic_share = item.get("topic_share", [])
                        topics_info = []
                        for topic in topic_share:
                            if "id" in topic and "display_name" in topic and "value" in topic:
                                topic_info = {
                                    "topic_id": topic["id"],
                                    "topic_name": topic["display_name"],
                                    "value": topic["value"]
                                }
                                topics_info.append(topic_info)
                        topics_json = json.dumps(topics_info) if topics_info else None

                        # 插入作者数据
                        if openalex_author_id and display_name and works_count is not None and cited_by_count is not None:
                            insert_into_author_table(cursor, openalex_author_id, orcid, display_name, display_name_alternatives_json,
                                                        works_count, cited_by_count, two_year_mean_citedness, h_index, 
                                                        two_year_cited_by_count, institutions_json, topics_json)
                    
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
    works_directory = "/root/openalex-snapshot/data/authors" 
    processed_files_file = "/root/openalex-snapshot/data/processed_authors_json.txt"  # 存储已处理文件路径的文件
    
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