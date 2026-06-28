"""主逻辑：从 Notion 拉取最新周报并通过飞书机器人发送。

每周日 21:00（北京时间）由 GitHub Action 定时触发。
所有配置通过环境变量（GitHub Secrets）注入。
"""

from __future__ import annotations

import os
import sys

from feishu import FeishuBot
from notion import NotionClient

# 周报中「摘要」「下周最重要任务」对应的 Notion 属性名，
# 可通过环境变量覆盖，默认使用中文属性名。
DEFAULT_SUMMARY_PROP = "摘要"
DEFAULT_NEXT_TASK_PROP = "下周最重要任务"


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"[错误] 缺少必需的环境变量: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    notion_token = _require_env("NOTION_TOKEN")
    database_id = _require_env("NOTION_DATABASE_ID")
    feishu_webhook = _require_env("FEISHU_WEBHOOK")

    summary_prop = os.environ.get("NOTION_PROP_SUMMARY", "").strip() or DEFAULT_SUMMARY_PROP
    next_task_prop = (
        os.environ.get("NOTION_PROP_NEXT_TASK", "").strip() or DEFAULT_NEXT_TASK_PROP
    )

    bot = FeishuBot(feishu_webhook)

    try:
        client = NotionClient(notion_token, database_id)
        report = client.get_latest_report(summary_prop, next_task_prop)
    except Exception as exc:  # noqa: BLE001 - 顶层兜底，确保失败时能告警
        print(f"[错误] 获取 Notion 周报失败: {exc}", file=sys.stderr)
        bot.send_text(f"获取 Notion 数据出错：{exc}")
        sys.exit(1)

    if report is None:
        print("[警告] Notion 数据库中没有任何记录，跳过发送。")
        return

    if report.is_empty():
        print("[警告] 最新周报的摘要与下周任务均为空，跳过发送。")
        return

    print(f"[信息] 已获取周报: 《{report.title}》(创建于 {report.created_time})")

    try:
        bot.send_card(
            title=report.title,
            summary=report.summary,
            next_task=report.next_task,
            url=report.url,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 发送飞书消息失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[成功] 周报已发送到飞书。")


if __name__ == "__main__":
    main()
