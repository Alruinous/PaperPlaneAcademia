from django.db import models

# Create your models here.
class Institution(models.Model):
    institution_id=models.AutoField(primary_key=True)
    openalex_institution_id=models.TextField()        # 机构的OpenAlex ID
    ror = models.TextField()  # 机构的 ROR (例如：https://ror.org/02czkny70)
    display_name = models.TextField()  # 机构名称
    display_name_alternatives=models.JSONField(null=True, blank=True)  # 机构的其他显示名称（如缩写或其他语言的名称）
    country_code = models.CharField(max_length=10)  # 国家代码（例如：中国是 "CN"）
    type = models.TextField()  # 机构类型（例如：education）
    homepage_url=models.TextField() # 该 URL 指向该机构的官方网站
    works_count=models.IntegerField()   # 该机构参与的总学术作品数量
    cited_by_count=models.IntegerField()    # 该机构的作品被引用的总次数
    two_yr_mean_citedness=models.IntegerField(default=0)  # 过去 2 年该机构作品的平均被引用次数
    two_yr_works_count=models.IntegerField(default=0)  # 过去两年内的作品数
    two_yr_cited_by_count=models.IntegerField(default=0)  # 过去两年内的引用次数
    h_index=models.IntegerField(default=0) # H-index
    oa_percent=models.FloatField(default=0) # 开放获取（Open Access）文章的比例
    wikidata=models.TextField()  # 该学科领域的 Wikidata 链接
    
    def __str__(self):
        return self.display_name