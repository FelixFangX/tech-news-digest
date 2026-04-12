# 技术快讯 | Tech News Digest

每日自动更新的技术快讯，聚合以下三个数据源：

- 🤖 **OpenAlex** — AI / ML 学术论文
- 🔥 **GitHub Trending** — 当日热门开源项目
- 💬 **StackOverflow** — 技术热点问答

## 📂 目录结构

```
tech-news-digest/
├── daily/              # 每日快讯文档
├── templates/          # MD 模板
├── scripts/            # 采集脚本
├── .github/
│   └── workflows/
│       └── daily-digest.yml   # GitHub Actions 自动采集
└── README.md
```

## ⚙️ 本地运行

```bash
# 克隆
git clone git@github.com:ColeFang/tech-news-digest.git
cd tech-news-digest

# 安装依赖
pip install requests

# 手动运行采集
python scripts/fetch_news.py

# GitHub Actions 自动采集（每日 00:00 UTC = 北京时间 08:00）
```

## 🔄 与 Obsidian 同步

Obsidian 直接克隆此仓库作为 Vault：

```bash
# 在 Obsidian vault 目录
git clone git@github.com:ColeFang/tech-news-digest.git ~/Documents/tech-news-digest
```

安装 **Obsidian Git** 插件，设置自动 push 时间，即可在 Obsidian 中阅读每日快讯，同时自动同步到 GitHub。

## 📅 文档命名规范

```
daily/YYYY-MM-DD.md   例: daily/2026-04-12.md
```

---

> 由 [Hermes Agent](https://github.com/ColeFang/hermes-agent) 自动维护
