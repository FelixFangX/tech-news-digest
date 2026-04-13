# 技术快讯 | Tech News Digest

每日自动更新的技术快讯，聚合以下三个数据源：

- 🤖 **OpenAlex** — AI / ML 学术论文
- 🔥 **GitHub Trending** — 当日热门开源项目
- 💬 **StackOverflow** — 技术热点问答

**AI 增强功能（A+B 进化阶段）：**

- **A1** 每日摘要 — LLM 生成今日技术形势导语
- **A2** 趋势分析 — 扫描过去 7 天识别热门/上升/新兴话题
- **B1/B2** 个性化排序 — 基于 `preferences.yaml` 匹配用户兴趣
- **B3** 多渠道分发 — Telegram / Email / WeChat

## 📂 目录结构

```
tech-news-digest/
├── daily/              # 每日快讯文档
│   └── trends-YYYY-MM-DD.md  # 周趋势报告
├── templates/           # MD 模板
├── scripts/
│   ├── fetch_news.py    # 主采集脚本
│   ├── summarize.py      # A1 每日摘要
│   ├── analyze_trends.py # A2 趋势分析
│   ├── rank.py          # B1/B2 个性化排序
│   ├── deliver.py       # B3 多渠道分发
│   └── llm_utils.py     # 统一 LLM 适配层
├── preferences.yaml.example  # 用户偏好配置模板
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
python scripts/fetch_news.py --trends           # 含 A2 趋势分析（过去7天）
python scripts/fetch_news.py --trends=14         # 含 A2 趋势分析（过去14天）
python scripts/fetch_news.py --deliver=telegram  # 采集 + 分发到 Telegram

# 配置 LLM（可选，用于 AI 判断和摘要）
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 或 MiniMax/Groq 等
export LLM_MODEL="gpt-4o"                           # 支持所有 OpenAI 兼容模型
```

## 📅 文档命名规范

```
daily/YYYY-MM-DD.md         # 每日快讯
daily/trends-YYYY-MM-DD.md  # 周趋势报告（A2）
```

## 🔧 个性化配置

复制配置模板并填写个人兴趣：

```bash
cp preferences.yaml.example preferences.yaml
# 编辑 preferences.yaml
```

## 🔄 与 Obsidian 同步

Obsidian 直接克隆此仓库作为 Vault：

```bash
# 在 Obsidian vault 目录
git clone git@github.com:ColeFang/tech-news-digest.git ~/Documents/tech-news-digest
```

安装 **Obsidian Git** 插件，设置自动 push 时间，即可在 Obsidian 中阅读每日快讯，同时自动同步到 GitHub。

---

> 由 [Hermes Agent](https://github.com/ColeFang/hermes-agent) 自动维护
