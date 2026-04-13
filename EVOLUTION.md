# tech-news-digest 进化方案 | Evolution Plan

## 目标
将 tech-news-digest 从「数据采集 + LLM 判断」升级为「AI 理解 + 趋势分析 + 个性化分发」的技术情报平台。

---

## 方案 A：自动摘要 + 趋势分析

### A1. 每日总摘要 (Daily Digest Summary)
在每份 daily MD 顶部，由 LLM 生成一段 3-5 句话的今日技术形势综述，作为快讯的「前言」。

**实现方式：**
- 采集完三类数据后，将今日所有 item 的 title + abstract/description 打包发给 LLM
- LLM 输出格式：「今日要点：...与此同时...值得关注的是...」
- 插入到 `## 🤖 AI 资讯` 之前

**Prompt 示例：**
```
你是一位技术主笔，为今日技术快讯撰写一段30字左右的导语，帮助读者快速了解今日最重要的技术趋势。
要求：简洁、有观点、不重复具体内容。
```

### A2. 趋势分析 (Trend Analysis)
识别近 7 天内重复出现的话题，标注为「热门持续」；发现单日异常集中的话题，标注为「今日焦点」。

**数据结构：**
```
TRENDS = {
  "rising": [...],      # 本周出现频率上升的话题
  "stable": [...],      # 持续热门话题
  "emerging": [...]     # 单日新焦点
}
```

**实现方式：**
- 在 `daily/` 目录下扫描过去 7 天的 `.md` 文件
- 提取每篇的 AI news topics + GitHub repo names + SO tags
- 用 embedding 或关键词匹配做话题聚合
- 输出一个 `weekly-trends.md` 汇总（可选，作为独立 section）

---

## 方案 B：个性化推荐 + 多渠道分发

### B1. 兴趣配置 (User Preferences)
用户可在 `preferences.yaml` 中配置关注领域：

```yaml
interests:
  - AI / LLM
  - Python
  - WebAssembly
  - CloudInfra

exclude:
  - JavaScript  # 过滤掉 JS 相关内容（如果你是后端开发者）

max_per_category: 5  # 每类最多显示条数

delivery:
  channels: ["wechat", "telegram"]  # 启用的分发渠道
```

采集脚本读取此配置，对原始数据进行**过滤 + 重排序**。

### B2. 精选推荐 (Personalized Ranking)
基于用户兴趣，对三类数据源做综合 ranking：

1. **关键词匹配** — interests 中的话题词命中文献/项目
2. **HotScore 计算** — `(stars * 1.0) + (votes * 2.0) + (answers * 1.5) - (recency_decay)`
3. **Diversity 调节** — 避免单一话题占满推荐位

最终输出按 `final_score` 降序排列的推荐列表。

### B3. 多渠道分发 (Multi-Channel Distribution)

#### WeChat (文字)
通过 WeChat ilink 协议发送，适配 `research-thinking-ai` 中已有的 WeChat 基础设施。

#### Telegram Bot
- Bot Token 通过环境变量 `TELEGRAM_BOT_TOKEN`
- Chat ID 通过 `TELEGRAM_CHAT_ID`
- 使用 Telegram Bot API 发送 Markdown 格式消息

#### Email (可选)
- SMTP 配置通过环境变量
- 使用 Python `smtplib` 发送 HTML 邮件

---

## 文件结构（进化后）

```
tech-news-digest/
├── scripts/
│   ├── fetch_news.py          # 原始采集脚本（保留）
│   ├── summarize.py           # A1: 每日摘要生成
│   ├── trends.py              # A2: 趋势分析
│   ├── rank.py                # B1: 个性化 ranking
│   ├── deliver.py             # B3: 多渠道分发
│   └── preferences.yaml       # 用户兴趣配置
├── daily/
│   ├── YYYY-MM-DD.md          # 每日快讯
│   └── weekly-trends/         # 周趋势分析
│       └── YYYY-WXX.md
├── templates/
│   ├── daily_template.md      # 原始模板（保留）
│   └── daily_ai_template.md   # AI 增强模板（含摘要+趋势位+AI判断）
├── preferences.yaml.example  # 配置示例
├── README.md
└── EVOLUTION.md               # 本文档
```

---

## 环境变量

| 变量 | 用途 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | LLM 调用 | `sk-...` |
| `OPENAI_BASE_URL` | API 端点 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型 | `gpt-4o-mini` |
| `GITHUB_TOKEN` | GitHub API | `ghp_...` |
| `WEIXIN_WEB_HOOK` | 微信 ilink | （已有基础设施）|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot | `123:abc...` |
| `TELEGRAM_CHAT_ID` | Telegram Chat | `-100123456` |
| `SMTP_HOST` / `SMTP_PORT` | Email SMTP | `smtp.gmail.com` / `587` |
| `SMTP_USER` / `SMTP_PASS` | Email 认证 | |

---

## 开发约定

- **不修改 `master` 分支** — Obsidian vault 直接克隆 master，任何 master 变更会影响笔记阅读
- **所有开发在 `feat-ai-evolution` 分支** — 通过 worktree `~/Documents/tech-news-digest-ai` 进行
- **最终合并后**再更新 master，或通过 PR 审阅后合并
- **偏好 YAML 配置**而非硬编码，业务逻辑与配置分离

---

## 实施顺序

1. ✅ **A1 每日摘要** — `scripts/summarize.py`，JSON-mode + max_tokens=800
2. ✅ **B1 兴趣配置** — `preferences.yaml` + `scripts/rank.py`
3. ✅ **B2 精选推荐** — `rank.py` 的 `match_score()` + `rank_content()`
4. ✅ **A2 趋势分析** — `scripts/analyze_trends.py` + `--trends` 标志，输出 `daily/trends-YYYY-MM-DD.md`
5. ✅ **B3 多渠道分发** — `scripts/deliver.py` 支持 Telegram / Email / WeChat / 飞书（Lark）
6. ✅ **GitHub Actions** — `.github/workflows/daily-digest.yml` 支持 `--trends` + `--deliver` 参数

## 渠道配置

| 渠道 | 配置项 | 说明 |
|------|--------|------|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | 向 @BotFather 创建 Bot |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO` | 支持 Gmail / 任意 SMTP |
| WeChat | `WEIXIN_ILINK_HOOK` | 微信 ilink 协议 |
| 飞书 Lark | `LARK_WEBHOOK_URL` | 群设置 → 添加机器人 → 自定义机器人 → Webhook |

所有配置项均可通过环境变量或 `preferences.yaml` 设置（环境变量优先）。
