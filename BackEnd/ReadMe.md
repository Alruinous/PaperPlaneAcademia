# welcome

## 关于构建数据库
    如果是本地建立数据库，在本地先建立一个空的数据库，然后修改PaperPlaneAcademicBackEnd/settings.py中数据库的配置：
    数据库名称和本地名称相同，密码为本机mysql服务的密码
    然后在终端运行：
    python manage.py makemigrations
    python manage.py migrate
