from django.db import models


class Paper(models.Model):
    paper_id = models.AutoField(primary_key=True)  # 论文的唯一标识符
    openalex_paper_id=models.TextField(default="")        # 论文的OpenAlex ID
    title = models.TextField()  # 论文标题，改为 TEXT 类型
    # 用于存储作者信息，包括作者名、位置、所属机构等，例如：
    # [{"id": "https://openalex.org/I4210112124","display_name": "Oliver H. Lowry"}...]
    authorships = models.JSONField(null=True, blank=True)  
    # 用于存储机构信息，例如：
    # [{"institution_id": "https://openalex.org/I5067833651","display_name": "Australian Society for Microbiology"}...]
    institutions = models.JSONField(null=True, blank=True)  # 参与论文撰写的机构
    publish_date = models.DateField()  # 论文的发表时间
    journal = models.CharField(max_length=1250, null=True, blank=True)  # 发表期刊名称
    volume = models.CharField(max_length=1250, null=True,
                              blank=True)  # 期刊卷号，改为 VARCHAR
    issue = models.CharField(max_length=1250, null=True,
                             blank=True)  # 期刊期号，改为 VARCHAR
    doi = models.CharField(max_length=1250, null=True,
                           blank=True)  # 数字对象标识符，取消 unique 属性
    favorites = models.PositiveIntegerField(default=0)  # 论文被收藏次数
    abstract = models.JSONField()  # 用于存储论文的简要概述，格式为字典
    keywords = models.JSONField(null=True, blank=True)  # 论文相关的关键词
    citation_count = models.PositiveIntegerField(default=0)  # 论文被引用的次数
    download_link = models.CharField(
        max_length=1500, null=True, blank=True)  # 论文的 PDF 下载链接，改为 VARCHAR
    original_link = models.CharField(
        max_length=1500, null=True, blank=True)  # 跳转到论文的在线界面，改为 VARCHAR
    references_works = models.JSONField(null=True, blank=True)  # 论文所参考的文献
    # 论文所属的研究领域，例如：[{ "id": "https://openalex.org/T11882", "display_name": "Biosynthesis and Engineering of Terpenoids" }, ...]
    research_fields = models.JSONField(null=True, blank=True)  
    # 论文的当前状态 Pending / Published / Rejected
    status = models.CharField(max_length=50)
    created_time = models.DateTimeField(auto_now_add=True)  # 记录的创建时间
    related_works = models.JSONField(null=True, blank=True)  # 相关文献

    def __str__(self):
        return self.title
