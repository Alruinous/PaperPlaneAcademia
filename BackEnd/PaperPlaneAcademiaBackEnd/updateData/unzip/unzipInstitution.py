import os
import gzip
import time
import json

# 解压 .gz 文件
def unzip_gz_file(file_path, extract_dir=None):
    try:
        if extract_dir is None:
            extract_dir = os.path.dirname(file_path)  # 使用当前文件夹作为解压目录

        # 提取原始文件名（不带 .gz 后缀）
        original_filename = os.path.splitext(os.path.basename(file_path))[0]
        # 构建解压后的文件路径
        output_file_path = os.path.join(extract_dir, original_filename + '.json')

        # 使用 gzip 模块解压文件
        with gzip.open(file_path, 'rb') as f_in:
            decompressed_data = f_in.read()

        # 将解压后的数据写入新文件
        with open(output_file_path, 'wb') as f_out:
            f_out.write(decompressed_data)

        print(f"文件 '{file_path}' 解压成功到 '{output_file_path}'")
    except Exception as e:
        print(f"解压文件失败: {e}")

# 将遍历到的 .gz 文件路径保存到 processed_institutions_gz.txt
def save_processed_files(file_path, gz_files):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for gz_file in gz_files:
                f.write(gz_file + '\n')
        print(f"已将已处理的 .gz 文件路径保存到 {file_path}")
    except Exception as e:
        print(f"保存文件路径时发生错误: {e}")

# 遍历目录并记录所有 .gz 文件路径（不进行解压）
def first_pass_processing(directory, processed_file):
    gz_files = set()  # 存储所有 .gz 文件路径
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.gz'):
                    file_path = os.path.join(root, file)
                    gz_files.add(file_path)  # 记录 .gz 文件路径
                    print(f"发现 .gz 文件：{file_path}")
        # 保存所有已处理的 .gz 文件路径到文件
        save_processed_files(processed_file, gz_files)
    except Exception as e:
        print(f"处理目录失败: {e}")
    return gz_files

# 监控目录中的新 .gz 文件并解压
def monitor_new_files(directory, processed_files, interval=10):
    print(f"开始监控目录：{directory}")
    while True:
        try:
            # 遍历当前目录，查找新的 .gz 文件
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.gz'):
                        file_path = os.path.join(root, file)
                        # 如果是新文件，进行解压
                        if file_path not in processed_files:
                            print(f"发现新文件：{file_path}")
                            unzip_gz_file(file_path)
                            processed_files.add(file_path)  # 记录已处理的文件
        except Exception as e:
            print(f"处理目录时发生错误: {e}")
        
        # 每隔一定时间检查一次新文件
        print(f"等待 {interval} 秒后继续检查...")
        time.sleep(interval)

# 主函数：首先遍历所有压缩包，记录已处理文件，然后开始监控新文件
def start_monitoring(local_dir):
    processed_file = "/root/openalex-snapshot/data/processed_institutions_gz.txt"  # 存储已处理 .gz 文件路径的文件
    if not os.path.exists(local_dir):
        print(f"目录 {local_dir} 不存在！请确认目录路径正确。")
        return

    # 第一次遍历，记录所有 .gz 文件路径
    print("开始第一次遍历，记录所有 .gz 文件...")
    processed_files = first_pass_processing(local_dir, processed_file)
    
    # 结束第一次遍历后，开始监控新文件的出现
    print("第一次遍历完成，开始监控新 .gz 文件...")
    monitor_new_files(local_dir, processed_files)

# 示例调用
local_dir = "/root/openalex-snapshot/data/institutions"  # 本地文件夹路径
start_monitoring(local_dir)