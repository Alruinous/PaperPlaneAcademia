### 2. authors
1. id: "https://openalex.org/A5071408405"
> OpenAlex 中该作者的唯一标识符

2. orcid: "https://orcid.org/0000-0002-0622-1395"
> 这是该作者的 ORCID（开放研究者和贡献者标识符）。ORCID 是一种全球性的、用于唯一标识研究人员的系统。此链接指向 Xing Shi 的 ORCID 页面。

3. display_name: "Xing Shi"
> 作者的展示名称，通常是该作者的全名。

4. display_name_alternatives: ["X. Shi", "X.G. Shi", "Shi Xing", "Xing Shi"]
> 该作者可能使用的其他展示名称，可能是该作者在不同出版物中使用的不同格式（例如，X. Shi 是缩写形式，Shi Xing 是姓在前的格式等）。

5. works_count: 62
> 该作者发表的总学术作品数量。表示该作者在 OpenAlex 中登记的所有学术作品数量。

6. cited_by_count: 554
> 该作者的所有作品被引用的总次数。这是衡量该作者学术影响力的一个指标。

7. summary_stats: 该字段包含了关于该作者的详细统计数据，具体包括以下几个子字段：
* 2yr_mean_citedness: 3.125
    过去两年该作者作品的平均被引用次数。表示过去两年内，该作者的作品平均每篇被引用 3.125 次。

* h_index: 13
    H-Index 是一个用于衡量学术影响力的指标。H-Index 为 13 表示该作者至少有 13 篇论文被引用了至少 13 次。

* i10_index: 16
    i10-Index 是另一种衡量学术影响力的指标，表示该作者有 16 篇论文至少被引用了 10 次。

* 2yr_cited_by_count: 216
    过去两年内该作者的作品被引用的总次数为 216。

8. last_known_institutions: 这是作者最近所属的机构列表。可以用来查看作者当前的隶属关系。每个隶属机构都有以下信息：
* institution：机构的详细信息（包括 ID、名称、国家代码等）。
* years：该作者在这些机构中工作的年份。
> * 例如：
    [
  {
    "id": "https://openalex.org/I16365422",
    "ror": "https://ror.org/02czkny70",
    "display_name": "Hefei University of Technology",
    "country_code": "CN",
    "country_id": "https://openalex.org/countries/CN",
    "type": "education",
    "type_id": "https://openalex.org/institution-types/education",
    "lineage": ["https://openalex.org/I16365422"]
  }
]



9. topic_share: 表示作者与特定学术主题的相关性及其在该主题中的贡献。topic_share 是一个包含多个条目的数组，每个条目表示作者与某一主题（topic）之间的关系。每个条目的字段如下：

* id: 每个学术主题的唯一标识符。它指向一个具体的学术主题的页面或描述。


> "topic_share": [
  {
    "id": "https://openalex.org/T11247",
    "display_name": "Plant Nutrient Uptake and Signaling Pathways",
    "subfield": {
      "id": "https://openalex.org/subfields/1110",
      "display_name": "Plant Science"
    },
    "field": {
      "id": "https://openalex.org/fields/11",
      "display_name": "Agricultural and Biological Sciences"
    },
    "domain": {
      "id": "https://openalex.org/domains/1",
      "display_name": "Life Sciences"
    },
    "value": 1.4e-05
  },
  {
    "id": "https://openalex.org/T11470",
    "display_name": "Symbiotic Nitrogen Fixation in Legumes",
    "subfield": {
      "id": "https://openalex.org/subfields/1110",
      "display_name": "Plant Science"
    },
    "field": {
      "id": "https://openalex.org/fields/11",
      "display_name": "Agricultural and Biological Sciences"
    },
    "domain": {
      "id": "https://openalex.org/domains/1",
      "display_name": "Life Sciences"
    },
    "value": 1.03e-05
  },
  {
    "id": "https://openalex.org/T10564",
    "display_name": "Microbial Nitrogen Cycling in Wastewater Treatment Systems",
    "subfield": {
      "id": "https://openalex.org/subfields/2310",
      "display_name": "Pollution"
    },
    "field": {
      "id": "https://openalex.org/fields/23",
      "display_name": "Environmental Science"
    },
    "domain": {
      "id": "https://openalex.org/domains/3",
      "display_name": "Physical Sciences"
    },
    "value": 6.5e-06
  }
]

    
