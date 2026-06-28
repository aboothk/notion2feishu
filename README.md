# notion2feishu

一个从 Notion 总结每周学习成果并发送到飞书的脚本。

每周日 **21:00（北京时间）** 由 GitHub Action 自动触发，从指定的 Notion 数据库中取出**最新创建**的一条周报，将其**摘要**和**下周最重要任务**通过飞书自定义机器人推送为一张交互式卡片。

## 目录结构

| 文件 | 职责 |
| --- | --- |
| `main.py` | 主逻辑：读取配置、串联 Notion 取数与飞书发送 |
| `notion.py` | 从 Notion 数据库查询最新周报并解析字段 |
| `feishu.py` | 通过飞书 webhook 发送消息（支持加签） |
| `.github/workflows/weekly-report.yml` | GitHub Action 定时任务 |

## 工作原理

1. 按 `created_time` 倒序查询 Notion 数据库，取最新创建的一条记录。
2. 自动识别 `title` 类型属性作为标题；按属性名读取「摘要」与「下周最重要任务」。
3. 组装成飞书交互式卡片并发送；若开启加签则附带签名。

## 准备工作

### 1. Notion

1. 在 https://www.notion.so/my-integrations 创建一个集成，得到 **Internal Integration Token**。
2. 打开你的周报数据库 → 右上角 `...` → `Connections` → 关联刚创建的集成。
3. 从数据库链接中复制 **Database ID**（链接里 32 位的那段）。
4. 数据库需要包含两个文本属性，默认名称为 **`摘要`** 和 **`下周最重要任务`**（名称可通过环境变量自定义）。标题列无需配置，脚本会自动识别。

### 2. 飞书

1. 在目标群里添加「自定义机器人」，复制 **Webhook 地址**。
2. 安全设置建议勾选「签名校验」，复制 **签名密钥**（即 `FEISHU_SECRET`）。

### 3. 配置 GitHub Secrets

在仓库 `Settings → Secrets and variables → Actions` 中添加：

| 类型 | 名称 | 说明 |
| --- | --- | --- |
| Secret | `NOTION_TOKEN` | Notion 集成 Token |
| Secret | `NOTION_DATABASE_ID` | Notion 数据库 ID |
| Secret | `FEISHU_WEBHOOK` | 飞书机器人 Webhook |
| Secret | `FEISHU_SECRET` | 飞书加签密钥（未开启加签可不填） |
| Variable | `NOTION_PROP_SUMMARY` | （可选）摘要属性名，默认 `摘要` |
| Variable | `NOTION_PROP_NEXT_TASK` | （可选）下周任务属性名，默认 `下周最重要任务` |

## 本地运行 / 调试

```bash
pip install -r requirement.txt
cp .env.example .env   # 填入你的配置

# 用一个临时脚本加载 .env 后运行，或直接导出环境变量：
export NOTION_TOKEN=...
export NOTION_DATABASE_ID=...
export FEISHU_WEBHOOK=...
export FEISHU_SECRET=...
python main.py
```

也可以在 GitHub 仓库的 `Actions` 页面手动触发 `Weekly Report to Feishu` 工作流（`workflow_dispatch`）进行测试。

## 定时说明

GitHub Action 的 cron 使用 UTC 时间。北京时间周日 21:00 对应 UTC 周日 13:00，因此：

```yaml
- cron: "0 13 * * 0"
```

> 注意：GitHub 定时任务在高峰期可能有几分钟到十几分钟的延迟，属正常现象。

## 参考

实现参考了 [lieeew/notion-rss](https://github.com/lieeew/notion-rss) 的整体思路。
