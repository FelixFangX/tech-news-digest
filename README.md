# Tech News Digest

**[English](./README.md)** | **[中文](./README_zh.md)**

Daily auto-updated tech newsletter, aggregating three data sources:

- 🤖 **OpenAlex** — AI / ML Academic Papers
- 🔥 **GitHub Trending** — Trending Repositories
- 💬 **StackOverflow** — Hot Q&A

## ✨ AI-Enhanced Features

| # | Feature | Description |
|---|---------|-------------|
| A1 | Daily Summary | LLM-generated overview |
| A2 | Trend Analysis | 7-day topic detection |
| B1/B2 | Personalized Ranking | Interest-based sorting |
| B3 | Multi-Channel Delivery | 4 channels supported |

**Bilingual Content:**

All daily digests include bilingual (Chinese + English) translations for paper titles, abstracts, and project descriptions, along with deep analysis and application scenario recommendations.

## 📂 Directory Structure

```
tech-news-digest/
├── daily/                    # Daily digests
│   └── trends-YYYY-MM-DD.md # Weekly trend reports
├── templates/                # Markdown templates
├── scripts/
│   ├── fetch_news.py         # Main pipeline
│   ├── summarize.py          # Daily summary
│   ├── analyze_trends.py     # Trend analysis
│   ├── rank.py               # Personalized ranking
│   ├── deliver.py            # Multi-channel delivery
│   └── llm_utils.py          # Unified LLM adapter
├── preferences.yaml.example  # Config template
├── EVOLUTION.md              # Evolution plan
└── README.md
```

## ⚙️ Getting Started

```bash
# Clone
git clone git@github.com:ColeFang/tech-news-digest.git
cd tech-news-digest

# Install dependencies
pip install requests pyyaml

# Run digest
python scripts/fetch_news.py                    # Plain text
python scripts/fetch_news.py --trends           # With trend analysis
python scripts/fetch_news.py --trends=14        # 14-day trends
python scripts/fetch_news.py --deliver=telegram # Fetch + deliver
```

## 🔑 LLM Configuration

All scripts use the **OpenAI-compatible protocol** (`/chat/completions` endpoint), supporting any provider:

| Provider | `LLM_BASE_URL` | `LLM_MODEL` Example |
|----------|-----------------|----------------------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` |
| **MiniMax** | `https://minimax.a7m.com.cn/v1` | `MiniMax-M2.7-highspeed` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4` |
| **Ollama** | `http://localhost:11434/v1` | `llama3` |

```bash
# Unified configuration
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

# Backward compatible
# OPENAI_API_KEY, OPENAI_BASE_URL, MINIMAX_API_KEY, MINIMAX_BASE_URL still work
```

**Priority:** `LLM_API_KEY` > `MINIMAX_API_KEY` > `OPENAI_API_KEY`

## 📅 File Naming

```
daily/YYYY-MM-DD.md         # Daily digest
daily/trends-YYYY-MM-DD.md  # Trend report
```

## 🔧 Personalization

Copy the config template and fill in your interests:

```bash
cp preferences.yaml.example preferences.yaml
# Edit preferences.yaml
```

## 📬 Delivery Channels

| Channel | Config | Description |
|---------|--------|-------------|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Create via @BotFather |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO` | Gmail / any SMTP |
| WeChat | `WEIXIN_ILINK_HOOK` | WeChat ilink |
| Lark | `LARK_WEBHOOK_URL` | Group Bot Webhook |

All settings can be configured via environment variables or `preferences.yaml` (env vars take priority).

## 🔄 Obsidian Sync

```bash
# In your Obsidian vault directory
git clone git@github.com:ColeFang/tech-news-digest.git ~/Documents/tech-news-digest
```

Install the **Obsidian Git** plugin, set auto-push intervals, and read daily digests directly in Obsidian.

---

> Maintained by [Hermes Agent](https://github.com/ColeFang/hermes-agent)
