from ftplib import FTP
import os
import shutil
import gzip
import json
import mysql.connector
from io import BytesIO
from datetime import datetime

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

# 插入数据到数据库表
def insert_into_paper_paper(cursor, doi,title,authors_string, institutions_string
                            , publish_date, favorites, abstract, keywords, citation_count, created_at, journal, volume, issue,
                            download_link, original_link, status):
    """
    将数据插入到 paper_paper 表中。
    :param cursor: 数据库游标
    :param paper_id: 论文的 ID
    :param doi: 论文的 DOI
    """
    query = "INSERT INTO papers_paper (doi, title,authors, institutions, publish_date, favorites, abstract, keywords, citation_count, created_time, journal, volume, issue, download_link, original_link, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (doi, title, authors_string, institutions_string, 
                           publish_date, favorites, abstract, keywords, citation_count, created_at, journal, volume, issue,
                           download_link, original_link, status))

from ftplib import FTP, error_perm
import os
import time

# 下载单个文件
def download_file(ftp, remote_path, local_path, retries=3, delay=5):
    try:
        print(f"准备下载: {remote_path}")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as local_file:
            ftp.retrbinary(f"RETR {remote_path}", local_file.write)
        print(f"文件 '{remote_path}' 下载成功到 '{local_path}'")
    except error_perm as e:
        print(f"FTP 权限错误: {e}")
    except Exception as e:
        if retries > 0:
            print(f"下载文件失败，重试 {retries} 次后将会放弃。错误信息: {e}")
            time.sleep(delay)  # 延时后重试
            download_file(ftp, remote_path, local_path, retries-1, delay)
        else:
            print(f"下载文件失败: {e}")

# 解压 .gz 文件
def unzip_gz_file(file_path, extract_dir=None):
    try:
        if extract_dir is None:
            extract_dir = os.path.splitext(file_path)[0]
        os.makedirs(extract_dir, exist_ok=True)

        original_filename = os.path.splitext(os.path.basename(file_path))[0]
        output_file_path = os.path.join(extract_dir, original_filename + '.json')

        with gzip.open(file_path, 'rb') as f_in:
            decompressed_data = f_in.read()

        with open(output_file_path, 'wb') as f_out:
            f_out.write(decompressed_data)

        print(f"文件 '{file_path}' 解压成功到 '{output_file_path}'")
        return output_file_path  # 返回解压后的文件路径
    except Exception as e:
        print(f"解压文件失败: {e}")
        return None

# 判断路径是否为目录
def is_directory(ftp, path):
    try:
        ftp.cwd(path)
        ftp.cwd('..')
        return True
    except Exception as e:
        return False

# 递归下载目录及文件
def download_directory(ftp, remote_dir, local_dir, retries=3, delay=5):
    try:
        print(f"正在切换到远程目录: {remote_dir}")
        ftp.cwd(remote_dir)

        items = ftp.nlst()  # 获取目录列表
        print(f"当前目录文件列表: {items}")

        for item in items:
            local_item_path = os.path.join(local_dir, item)

            if is_directory(ftp, item):
                if not os.path.exists(local_item_path):
                    os.makedirs(local_item_path)
                    print(f"创建目录 '{local_item_path}'")
                download_directory(ftp, item, local_item_path, retries, delay)  # 递归调用时传递 retries 和 delay
            else:
                download_file(ftp, item, local_item_path, retries, delay)  # 同样传递 retries 和 delay
                if item.endswith('.gz'):
                    extracted_file = unzip_gz_file(local_item_path, extract_dir=os.path.join(local_dir, os.path.splitext(item)[0]))
                    if extracted_file:
                        process_json_file(extracted_file)  # 处理解压后的 JSON 文件
                    os.remove(local_item_path)  # 删除下载的压缩包
        ftp.cwd('..')

    except Exception as e:
        print(f"下载目录失败: {e}")


# 递归处理 JSON 文件并插入数据库
def process_json_file(json_file_path):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        #print(item)
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
                        abstract_inverted_index_json = json.dumps(abstract_inverted_index)

                        # 关键词：读取 topics 数组中的 display_name 字段，并拼接成一个长字符串
                        topics = item.get("topics", [])
                        topic_names = [topic['display_name'] for topic in topics if 'display_name' in topic]
                        #topics_string = ', '.join(topic_names)
                        topics_json=json.dumps(topic_names)

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

                        # 状态
                        status="Published"
                        
                        # 确保字段值不会为 None 或空字符串，若为空则使用默认值
                        doi = doi or ''
                        title = title or ''
                        publish_date = publish_date or None
                        cited_by_count=cited_by_count or 0
                        journal = journal or ''
                        volume = volume or ''
                        issue = issue or ''
                        pdf_url = pdf_url or ''
                        landing_page_url = landing_page_url or ''
                        status = status or 'Published'


                        if paper_id and doi and title and authors_json and institutions_json:
                            insert_into_paper_paper(cursor, doi,title,authors_json, institutions_json,
                                                    publish_date, favorites, abstract_inverted_index_json,
                                                    topics_json, cited_by_count, current_time, journal, volume, issue,
                                                    pdf_url, landing_page_url, status)
                        
                    
                
                    
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

    os.remove(json_file_path)  # 删除已处理的 JSON 文件


# FTP 连接与下载主程序
def ftp_download_recursive(ftp_host, ftp_user, ftp_pass, remote_dir, local_dir, ftp_port=21, retries=5, delay=10):
    attempt = 0  # 初始化连接尝试计数
    while attempt < retries:
        try:
            # 创建 FTP 连接
            ftp = FTP()
            ftp.set_debuglevel(2)  # 启用调试输出（可帮助诊断问题）
            ftp.connect(ftp_host, ftp_port, timeout=120)  # 设置连接超时
            ftp.set_pasv(True)  # 启用被动模式
            ftp.login(ftp_user, ftp_pass)

            # 创建本地目录
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # 调用递归下载函数
            download_directory(ftp, remote_dir, local_dir, retries, delay)

            ftp.quit()
            print(f"FTP 下载和解压完成。")
            break  # 如果成功，退出循环
        except (ConnectionResetError, error_perm, error_temp) as e:
            # 捕获连接错误并重试
            attempt += 1
            print(f"尝试 {attempt}/{retries} 连接失败，错误信息: {e}")
            if attempt < retries:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)  # 等待一段时间后重试
            else:
                print("达到最大重试次数，停止尝试。")
        except Exception as e:
            print(f"发生未知错误: {e}")
            break  # 发生其他错误时直接退出循环

# 示例调用
ftp_host = '211.71.15.54'
ftp_user = 'OpenAlex'
ftp_pass = 'OpenAlex@G304'
remote_dir = 'openalex-snapshot/data/works'
local_dir = "C:/Users/16584/Documents/Software/downloadedData/works"
ftp_port = 16304

ftp_download_recursive(ftp_host, ftp_user, ftp_pass, remote_dir, local_dir, ftp_port=ftp_port)
