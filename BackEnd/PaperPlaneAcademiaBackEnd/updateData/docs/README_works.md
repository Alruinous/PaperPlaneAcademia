### 1. works
1. id: "https://openalex.org/W1775749144"
> 文章在OpenAlex中的唯一标识符。这个链接指向了OpenAlex平台上的该文献页面。

2. doi: "https://doi.org/10.1016/s0021-9258(19)52451-6"
> 解释: 文章的DOI（数字对象标识符）。DOI是一个永久的文献标识符，可以用来在线查找文章。

3. doi_registration_agency: "Crossref"
> 解释: 文章的DOI由哪个注册机构注册的，这里是 Crossref，是全球知名的DOI注册机构。

4. display_name & title:
* "display_name": "PROTEIN MEASUREMENT WITH THE FOLIN PHENOL REAGENT",
* "title": "PROTEIN MEASUREMENT WITH THE FOLIN PHENOL REAGENT"
> 文章的显示名称和标题。这里的标题与显示名称相同，表示这篇文章是关于使用Folin Phenol试剂进行蛋白质测量的。

5. publication_year & publication_date
* "publication_year": 1951,
* "publication_date": "1951-11-01"
> 文章的出版年份和具体的出版日期。此文章发表于1951年11月1日。

6. language: "en"
> 文章的语言代码，这里是 en 表示英文。

7. primary_location
* "primary_location": {
  "source": {
    "id": "https://openalex.org/S140251998",
    "issn_l": "0021-9258",
    "issn": ["0021-9258", "1067-8816", "1083-351X"],
    "display_name": "Journal of Biological Chemistry",
    "publisher": "Elsevier BV",
    "host_organization": "https://openalex.org/P4310320990",
    "host_organization_name": "Elsevier BV",
    "type": "journal"
  }
}
> 文章的主要来源信息。
source: 文章发表的期刊。
id 是期刊在OpenAlex上的唯一标识符。
issn_l 是期刊的标准国际连续出版物编号（ISSN）。
display_name 是期刊的名称，Journal of Biological Chemistry。
publisher 是出版商，Elsevier BV。
type 表示这是一个期刊。

8. best_oa_location
* "best_oa_location": {
  "source": {
    "id": "https://openalex.org/S140251998",
    "issn_l": "0021-9258",
    "issn": ["0021-9258", "1067-8816", "1083-351X"],
    "display_name": "Journal of Biological Chemistry",
    "publisher": "Elsevier BV",
    "host_organization": "https://openalex.org/P4310320990",
    "host_organization_name": "Elsevier BV",
    "is_oa": true
  },
  "pdf_url": null,
  "landing_page_url": "https://doi.org/10.1016/s0021-9258(19)52451-6"
}
> 文章的开放获取信息（OA：Open Access）。
is_oa 表示文章是开放获取的，即可以免费访问。
pdf_url 和 landing_page_url 给出文章在线访问的链接。此文的PDF链接为空，但可以通过DOI链接访问文章页面。

9. authorships
* "authorships": [
  {
    "author_position": "first",
    "author": {"id": "https://openalex.org/A5067833651", "display_name": "Oliver H. Lowry"},
    "institutions": [{"id": "https://openalex.org/I204465549", "display_name": "Washington University in St. Louis"}],
    "countries": ["US"]
  }
]
> 文章的作者及其所在机构。
author_position 指作者在文章中的位置，first 表示第一作者。
author 中的 display_name 给出了作者的名字，Oliver H. Lowry。
institutions 表示该作者所属的机构，Washington University in St. Louis。
countries 给出作者所属的国家，这里是 美国。

10. cited_by_count: 318208
> 文章被引用的总次数。这篇文章被引用了 318208 次。
11. biblio
* "biblio": {
  "volume": "193",
  "issue": "1",
  "first_page": "265",
  "last_page": "275"
}
> 文章在期刊中的具体出版信息。
volume 和 issue 是期刊的卷号和期号。
first_page 和 last_page 表示文章在期刊中的页码范围。

12. topics
* "topics": [
  {
    "id": "https://openalex.org/T10602",
    "display_name": "Glycosylation in Health and Disease",
    "subfield": {"id": "https://openalex.org/subfields/1312", "display_name": "Molecular Biology"}
  }
]
> 文章的研究主题。
display_name 表示文章涉及的具体研究主题，Glycosylation in Health and Disease。
subfield 是与该主题相关的更细的学科领域，Molecular Biology（分子生物学）。
13. abstract_inverted_index
* "abstract_inverted_index": {
  "Since": [0], "1922": [1], "when": [2], "Wu": [3], ...
}
> 文章摘要的倒排索引。这个字段用于搜索和文本分析，列出了文章摘要中出现的关键词和它们的位置。
14. related_works
* "related_works": [
  "https://openalex.org/W4387497383",
  "https://openalex.org/W2948807893"
]
> 与当前文章相关的其他文章。这是一些可能与该文献内容有关或引用了该文献的其他文章链接。
15. updated_date & created_date
* "updated_date": "2024-09-26T05:57:04.825023",
* "created_date": "2016-06-24"
> 文章的更新时间和创建时间。
* created_date 表示文章在数据库中的首次创建时间。
* updated_date 表示文章的最新更新时间。
