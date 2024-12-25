import os
import json
import mysql.connector
from datetime import datetime

# 设置数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'paperbackenddb',  
        'USER': 'root',  
        'PASSWORD': 'wen03liuyi',  
        'HOST': 'localhost',
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

# 插入数据到数据库表
def insert_into_paper_paper(cursor, doi,title,authors_string, institutions_string
                            , publish_date, favorites, abstract, topics, keywords, citation_count, created_at, journal, volume, issue,
                            download_link, original_link, status, referenced_works_json):
    """
    将数据插入到 paper_paper 表中。
    :param cursor: 数据库游标
    :param paper_id: 论文的 ID
    :param doi: 论文的 DOI
    """
    query = "INSERT INTO papers_paper (doi, title,authors, institutions, publish_date, favorites, abstract, research_fields, keywords, citation_count, created_time, journal, volume, issue, download_link, original_link, status, references) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (doi, title, authors_string, institutions_string, 
                           publish_date, favorites, abstract, topics, keywords, citation_count, created_at, journal, volume, issue,
                           download_link, original_link, status, referenced_works_json))

# 递归读取文件夹中的 JSON 文件并处理数据
def process_json_files_in_directory(directory):
    """
    递归读取目录下的所有 JSON 文件并插入数据到数据库。
    :param directory: 需要读取的文件夹路径
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_file_path = os.path.join(root, file)
                process_json_file(json_file_path)

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

                        paper_id = item.get("id")
                        doi = item.get("doi")  # 假设 "doi" 是正确的字段名，而不是 "name"
                        title=item.get("title")
                        
                        # 读取作者列表，并拼接成一个JSON 字符串
                        authorships = item.get("authorships", [])
                        author_names = [authorship['author']['display_name'] for authorship in authorships if 'author' in authorship and 'display_name' in authorship['author']]
                        #authors_string = ', '.join(author_names)
                        authors_json=json.dumps(author_names)  # 转换为 JSON 字符串


                        # 读取作者的所有机构名称，并拼接成一个JSON 字符串
                        institution_names = []
                        for authorship in authorships:
                            institutions = authorship.get('institutions', [])
                            for institution in institutions:
                                if 'display_name' in institution:
                                    institution_names.append(institution['display_name'])
                        
                        #institutions_string = ', '.join(institution_names)
                        institutions_json=json.dumps(institution_names)  # 转换为 JSON 字符串

                        publish_date=item.get("publication_date")
                        # 发表日期
                        if publish_date:
                        # 假设 publication_date 是一个 ISO 格式的字符串（YYYY-MM-DD）
                        # 如果 publication_date 不是字符串，可以将其转换为 datetime 对象
                            if isinstance(publish_date, str):
                            # 尝试将字符串转换为日期格式
                                try:
                                    publish_date = datetime.strptime(publish_date, "%Y-%m-%d").date()
                                except ValueError:
                                    print(f"警告: publication_date 格式无效，无法转换: {publish_date}")
                                    publish_date = None
                            elif isinstance(publish_date, datetime):
                                # 如果已经是 datetime 对象，直接转换为 date
                                publish_date = publish_date.date()
                        else:
                            publish_date = None

                        favorites=0

                        # 摘要
                        abstract_inverted_index = item.get("abstract_inverted_index", {})
                        abstract_inverted_index_string = json.dumps(abstract_inverted_index)

                        # 领域：读取 topics 数组中的 display_name 字段，并拼接成一个长字符串
                        topics = item.get("topics", [])
                        topic_names = [topic['display_name'] for topic in topics if 'display_name' in topic]
                        #topics_string = ', '.join(topic_names)
                        topics_json=json.dumps(topic_names)

                        # 关键词: 读取 keywords 数组中的 display_name 字段，并拼接成一个长字符串
                        keywords = item.get("keywords", [])
                        keywords_names = [keywords['display_name'] for keyword in keywords if 'display_name' in keyword]
                        keywords_json=json.dumps(keywords_names)

                        # 引用次数
                        cited_by_count=item.get("cited_by_count")

                        # 创建时间
                        current_time = datetime.now()
                        
                        # 获取期刊的卷号和期号
                        biblio = item.get("biblio", {})
                        if(biblio is None):
                            volume = ""
                            issue = ""
                        else:
                            volume = biblio.get("volume", "")
                            issue = biblio.get("issue", "")

                        # 获取 best_oa_location 中的 pdf_url 和 landing_page_url(下载链接和原链接)
                        # 获取最佳开放获取位置的出版社和显示名称
                        best_oa_location = item.get("best_oa_location", {})
                        if(best_oa_location is None):
                            pdf_url=""
                            landing_page_url=""
                            journal = ""

                        else:
                            pdf_url = best_oa_location.get("pdf_url", "")
                            landing_page_url = best_oa_location.get("landing_page_url", "")
                            source = best_oa_location.get("source", {})
                            # 确保 source 不为 None
                            if source is None:
                                journal = ""
                            else:
                                publisher = source.get("publisher", "")
                                display_name = source.get("display_name", "")
                                
                                if(publisher is None): journal=display_name
                                elif(display_name is None): journal=publisher
                                else: journal = publisher+display_name

                        # 当前论文的参考文献
                        # 读取 referenced_works 列表
                        referenced_works = item.get("referenced_works", [])
                        # 提取出每个 URL（如果需要的话，可以进一步处理或验证 URL 格式）
                        referenced_works_json = json.dumps(referenced_works)

                        # 当前论文的相关文献
                        #related_works=item.get("related_works", [])
                        #related_works_json = json.dumps(related_works)

                        # 状态
                        status="Published"

                        if paper_id and doi and title and authors_json and institutions_json:
                            insert_into_paper_paper(cursor, doi,title,authors_json, institutions_json,
                                                    publish_date, favorites, abstract_inverted_index_string,
                                                    topics_json,keywords_json, cited_by_count, current_time, journal, volume, issue,
                                                    pdf_url, landing_page_url, status, referenced_works_json)
                        
                    
                
                    
                    except json.JSONDecodeError as e:
                        print(f"文件 {json_file_path} 中的某一行解析失败，内容：{line[:100]}...\n错误：{e}")

        connection.commit()
        print(f"成功插入 {json_file_path} 中的数据到数据库。")

    except Exception as e:
        connection.rollback()
        print(f"处理文件 {json_file_path} 时发生错误: {e}")

    finally:
        cursor.close()
        connection.close()

# 主程序入口
if __name__ == "__main__":
    # 设置要读取的工作目录
    works_directory = "C:/Users/16584/Documents/Software/downloadedData/works"
    
    # 开始处理 JSON 文件
    process_json_files_in_directory(works_directory)
    print("所有 JSON 文件处理完毕。")
