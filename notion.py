"""Notion 数据获取模块。

负责从指定的 Notion 数据库中查询最新创建的一条周报，
并解析出标题、摘要、下周最重要任务等字段。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import requests

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
REQUEST_TIMEOUT = 30


@dataclass
class WeeklyReport:
    """一条周报的结构化数据。"""

    title: str
    summary: str
    next_task: str
    url: str
    created_time: str

    def is_empty(self) -> bool:
        """摘要和下周任务都为空时视为无有效内容。"""
        return not (self.summary.strip() or self.next_task.strip())


class NotionClient:
    """对 Notion 官方 API 的轻量封装。"""

    def __init__(self, token: str, database_id: str) -> None:
        if not token:
            raise ValueError("缺少 Notion Token (NOTION_TOKEN)")
        if not database_id:
            raise ValueError("缺少 Notion 数据库 ID (NOTION_DATABASE_ID)")
        self.token = token
        self.database_id = database_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )

    def query_latest(self) -> Optional[dict[str, Any]]:
        """按创建时间倒序查询，返回最新创建的一条记录（page 对象）。"""
        url = f"{NOTION_API_BASE}/databases/{self.database_id}/query"
        payload = {
            "sorts": [
                {"timestamp": "created_time", "direction": "descending"}
            ],
            "page_size": 1,
        }
        resp = self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(
                f"查询 Notion 数据库失败: {resp.status_code} {resp.text}"
            )
        results = resp.json().get("results", [])
        return results[0] if results else None

    def get_latest_report(
        self, summary_prop: str, next_task_prop: str
    ) -> Optional[WeeklyReport]:
        """获取最新一条周报并解析为 WeeklyReport。

        title 属性按类型自动识别（Notion 每个数据库有且仅有一个 title 属性），
        摘要与下周任务按传入的属性名读取。
        """
        page = self.query_latest()
        if page is None:
            return None

        props: dict[str, Any] = page.get("properties", {})
        return WeeklyReport(
            title=self._extract_title(props),
            summary=self._extract_plain_text(props.get(summary_prop)),
            next_task=self._extract_plain_text(props.get(next_task_prop)),
            url=page.get("url", ""),
            created_time=page.get("created_time", ""),
        )

    @staticmethod
    def _extract_title(props: dict[str, Any]) -> str:
        """自动找到类型为 title 的属性并返回其纯文本。"""
        for prop in props.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                return NotionClient._join_rich_text(prop.get("title", []))
        return ""

    @staticmethod
    def _extract_plain_text(prop: Optional[dict[str, Any]]) -> str:
        """从一个属性对象中提取纯文本，兼容 rich_text / title 等类型。"""
        if not isinstance(prop, dict):
            return ""
        prop_type = prop.get("type")
        if prop_type in ("rich_text", "title"):
            return NotionClient._join_rich_text(prop.get(prop_type, []))
        if prop_type == "select":
            select = prop.get("select")
            return select.get("name", "") if select else ""
        return ""

    @staticmethod
    def _join_rich_text(rich_text: list[dict[str, Any]]) -> str:
        """拼接 rich_text 数组中的纯文本。"""
        return "".join(item.get("plain_text", "") for item in rich_text).strip()
