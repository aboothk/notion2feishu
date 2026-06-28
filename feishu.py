"""飞书消息发送模块。

通过飞书自动化流程（Flow）Webhook 触发器发送周报消息。
Flow 按 JSON 路径取值，payload 结构需与流程中配置的变量路径对应：
  - 消息标题  → card.header.title.content
  - 消息内容  → card.body.elements[0].content
  - 跳转 URL  → card.body.url
"""

from __future__ import annotations

from typing import Any

import requests

REQUEST_TIMEOUT = 30


class FeishuBot:
    """飞书 Flow Webhook 触发器封装。"""

    def __init__(self, webhook: str) -> None:
        if not webhook:
            raise ValueError("缺少飞书 Webhook 地址 (FEISHU_WEBHOOK)")
        self.webhook = webhook

    def _post(self, body: dict[str, Any]) -> None:
        resp = requests.post(self.webhook, json=body, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(f"发送飞书消息失败: HTTP {resp.status_code} {resp.text}")
        data = resp.json()
        code = data.get("code", 0)
        if code != 0:
            raise RuntimeError(f"发送飞书消息失败: {data}")

    def send_card(
        self,
        title: str,
        summary: str,
        next_task: str,
        url: str,
    ) -> None:
        """发送周报卡片。"""
        content = (
            f"**📋 本周摘要**\n{summary or '_（无）_'}\n\n"
            f"**🎯 下周最重要任务**\n{next_task or '_（无）_'}"
        )
        body: dict[str, Any] = {
            "card": {
                "header": {
                    "title": {"content": title or "每周周报"}
                },
                "body": {
                    "elements": [{"content": content}],
                    "url": url,
                },
            }
        }
        self._post(body)

    def send_text(self, content: str) -> None:
        """发送纯文本告警（Notion 取数失败时使用）。"""
        body: dict[str, Any] = {
            "card": {
                "header": {
                    "title": {"content": "⚠️ 周报推送失败"}
                },
                "body": {
                    "elements": [{"content": content}],
                    "url": "",
                },
            }
        }
        self._post(body)
