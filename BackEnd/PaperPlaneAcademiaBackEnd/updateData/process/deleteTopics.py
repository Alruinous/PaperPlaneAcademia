import pymysql

# 数据库连接配置
host = '113.44.138.144'          # 数据库主机
user = 'root'               # 数据库用户名
password = '123456'       # 数据库密码
database = 'paperbackenddb' # 数据库名称

# 连接到数据库
connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

batch_size = 10000  # 每批次删除的条目数
offset = 0

try:
    with connection.cursor() as cursor:
        while True:
            # 1. 创建一个临时表来存储每个 openalex_topic_id 的最小 topic_id
            cursor.execute("""
            CREATE TEMPORARY TABLE temp_min_topic_ids AS
            SELECT MIN(topic_id) AS topic_id
            FROM topics_topic
            GROUP BY openalex_topic_id;
            """)
        
            # 2. # 分批删除不在临时表中的 topic_id
            cursor.execute(f"""
            DELETE FROM topics_topic
            WHERE topic_id NOT IN (SELECT topic_id FROM temp_min_topic_ids)
            LIMIT {batch_size} OFFSET {offset};
            """)
        
            # 3. 删除临时表
            cursor.execute("DROP TEMPORARY TABLE temp_min_topic_ids;")

            print("delete suscess partially.")
        
            # 提交事务
            connection.commit()
            # 如果删除的记录数少于批次大小，说明删除完成
            if cursor.rowcount < batch_size:
                break
            # 增加偏移量，进行下一批次删除
            offset += batch_size
        
finally:
    connection.close()
