# 技术快讯

**[English](./README.md)** | **[中文](./README_zh.md)**

每日自动更新的技术快讯，聚合以下三个数据源：

- 🤖 **OpenAlex** — AI / ML 学术论文
- 🔥 **GitHub Trending** — 当日热门开源项目
- 💬 **StackOverflow** — 技术热点问答

## ✨ AI 增强功能

| 编号 | 功能 | 说明 |
|------|------|------|
| A1 | 每日摘要 | LLM 生成今日技术形势导语 |
| A2 | 趋势分析 | 扫描过去 7 天识别热门/上升/新兴话题 |
| B1/B2 | 个性化排序 | 基于 `preferences.yaml` 匹配用户兴趣 |
| B3 | 多渠道分发 | Telegram / Email / WeChat / 飞书 Lark |

**双语内容：**

每日快讯中，AI 论文标题、摘要、GitHub 项目描述均提供中英双语翻译，并附带深度分析和落地场景推荐。

## 📂 目录结构

```
tech-news-digest/
├── daily/                    # 每日快讯文档
│   └── trends-YYYY-MM-DD.md # 周趋势报告
├── templates/                # MD 模板
├── scripts/
│   ├── fetch_news.py         # 主采集脚本
│   ├── summarize.py          # 每日摘要
│   ├── analyze_trends.py     # 趋势分析
│   ├── rank.py               # 个性化排序
│   ├── deliver.py            # 多渠道分发
│   └── llm_utils.py          # 统一 LLM 适配层
├── preferences.yaml.example  # 用户偏好配置模板
├── EVOLUTION.md              # 进化方案文档
└── README.md
```

## ⚙️ 本地运行

```bash
# 克隆
git clone git@github.com:ColeFang/tech-news-digest.git
cd tech-news-digest

# 安装依赖
pip install requests pyyaml

# 运行采集
python scripts/fetch_news.py                    # 纯文本版
python scripts/fetch_news.py --trends           # 含趋势分析
python scripts/fetch_news.py --trends=14        # 含 14 天趋势分析
python scripts/fetch_news.py --deliver=telegram # 采集 + 分发
```

## 🔑 LLM 配置

所有脚本统一使用 **OpenAI 兼容协议**（`/chat/completions` 端点），支持以下任意提供商：

| 提供商 | `LLM_BASE_URL` | `LLM_MODEL` 示例 |
|--------|-----------------|-------------------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` |
| **MiniMax** | `https://minimax.a7m.com.cn/v1` | `MiniMax-M2.7-highspeed` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4` |
| **Ollama** | `http://localhost:11434/v1` | `llama3` |

```bash
# 统一配置方式
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

# 向后兼容旧变量名
# OPENAI_API_KEY, OPENAI_BASE_URL, MINIMAX_API_KEY, MINIMAX_BASE_URL 仍可使用
```

**环境变量优先级：** `LLM_API_KEY` > `MINIMAX_API_KEY` > `OPENAI_API_KEY`

## 📅 文档命名规范

```
daily/YYYY-MM-DD.md         # 每日快讯
daily/trends-YYYY-MM-DD.md  # 周趋势报告
```

## 🔧 个性化配置

复制配置模板并填写个人兴趣：

```bash
cp preferences.yaml.example preferences.yaml
# 编辑 preferences.yaml
```

## 📬 分发渠道配置

| 渠道 | 配置项 | 说明 |
|------|--------|------|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | 向 @BotFather 创建 Bot |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO` | 支持 Gmail / 任意 SMTP |
| WeChat | `WEIXIN_ILINK_HOOK` | 微信 ilink 协议 |
| 飞书 Lark | `LARK_WEBHOOK_URL` | 群机器人 Webhook |

所有配置项均可通过环境变量或 `preferences.yaml` 设置（环境变量优先）。

## 🔄 与 Obsidian 同步

```bash
# 在 Obsidian vault 目录
git clone git@github.com:ColeFang/tech-news-digest.git ~/Documents/tech-news-digest
```

安装 **Obsidian Git** 插件，设置自动 push 时间，即可在 Obsidian 中阅读每日快讯。

---

> 由 [Hermes Agent](https://github.com/ColeFang/hermes-agent) 自动维护
