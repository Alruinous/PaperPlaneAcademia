from ftplib import FTP
import os
import shutil
import gzip
import tarfile
import json
from io import BytesIO

# 下载单个文件
def download_file(ftp, remote_path, local_path):
    try:
        print(f"准备下载: {remote_path}")
        with open(local_path, 'wb') as local_file:
            ftp.retrbinary(f"RETR {remote_path}", local_file.write)
        print(f"文件 '{remote_path}' 下载成功到 '{local_path}'")
    except Exception as e:
        print(f"下载文件失败: {e}")


def unzip_gz_file(file_path, extract_dir=None):
    try:
        if extract_dir is None:
            extract_dir = os.path.splitext(file_path)[0]
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
 
        # 提取原始文件名（不带.gz后缀）
        original_filename = os.path.splitext(os.path.basename(file_path))[0]
        # 构建解压后的文件路径
        output_file_path = os.path.join(extract_dir, original_filename + '.json')
 
        # 使用gzip模块解压文件
        with gzip.open(file_path, 'rb') as f_in:
            decompressed_data = f_in.read()
 
        # 将解压后的数据写入新文件
        with open(output_file_path, 'wb') as f_out:
            f_out.write(decompressed_data)
 
        # 注意：这里我们假设gzip文件的内容是二进制数据（对于JSON来说，通常是UTF-8编码的文本，但作为二进制处理是安全的）
        # 如果你知道它是文本数据并且想要以文本模式写入，你可以解码它：
        # decompressed_text = decompressed_data.decode('utf-8')
        # 然后以文本模式写入：
        # with open(output_file_path, 'w', encoding='utf-8') as f_out:
        #     f_out.write(decompressed_text)
 
        print(f"文件 '{file_path}' 解压成功到 '{output_file_path}'")
    except Exception as e:
        print(f"解压文件失败: {e}")

# 递归下载文件夹
def download_directory(ftp, remote_dir, local_dir):
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
                download_directory(ftp, item, local_item_path)
            else:
                if item.endswith('.gz'):  # 检查文件是否为.gz格式
                    download_file(ftp, item, local_item_path)
                    unzip_gz_file(local_item_path, extract_dir=os.path.join(local_dir, os.path.splitext(item)[0]))  # 解压文件
                    #unzipped_data = unzip_gz_json(local_item_path)
                else:
                    download_file(ftp, item, local_item_path)
        ftp.cwd('..')

    except Exception as e:
        print(f"下载目录失败: {e}")

# 判断路径是否为目录
def is_directory(ftp, path):
    try:
        ftp.cwd(path)
        ftp.cwd('..')
        return True
    except Exception as e:
        return False

# 主函数：递归下载远程目录
def ftp_download_recursive(ftp_host, ftp_user, ftp_pass, remote_dir, local_dir, ftp_port=21):
    try:
        ftp = FTP()
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        download_directory(ftp, remote_dir, local_dir)

        ftp.quit()
        print(f"FTP 下载和解压完成。")
    except Exception as e:
        print(f"FTP连接、下载或解压过程中发生错误: {e}")

# 示例调用
ftp_host = '211.71.15.54'
ftp_user = 'OpenAlex'
ftp_pass = 'OpenAlex@G304'
remote_dir = 'openalex-snapshot/data/works'
local_dir = "C:/Users/16584/Documents/Software/downloadedData/works"
ftp_port = 16304  # 注意：通常FTP端口是21，除非您的服务器使用了非标准端口

ftp_download_recursive(ftp_host, ftp_user, ftp_pass, remote_dir, local_dir, ftp_port=ftp_port)