# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import arxiv
import json
import os
import sys
from datetime import datetime, timedelta

from scrapy.exceptions import DropItem


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)
        # 从环境变量读取排除关键词（逗号分隔），标题或摘要包含任一关键词的论文将被过滤
        negative_kw_raw = os.environ.get("NEGATIVE_KEYWORDS", "").strip()
        self.negative_keywords = [
            kw.strip().lower()
            for kw in negative_kw_raw.split(",")
            if kw.strip()
        ]

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        search = arxiv.Search(
            id_list=[item["id"]],
        )
        paper = next(self.client.results(search))
        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = paper.categories
        item["comment"] = paper.comment
        item["summary"] = paper.summary

        # 若设置了 NEGATIVE_KEYWORDS，标题或摘要包含任一关键词则丢弃该论文
        if self.negative_keywords:
            text = f"{item['title']} {item['summary']}".lower()
            for kw in self.negative_keywords:
                if kw in text:
                    raise DropItem(
                        f"Dropped paper {item['id']}: title/summary contains negative keyword '{kw}'"
                    )

        return item