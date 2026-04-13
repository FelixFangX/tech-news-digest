#!/usr/bin/env python3
"""
技术快讯采集脚本 v2
每天自动采集: OpenAlex AI论文 · GitHub 高星活跃项目 · StackOverflow 热点
每篇加入个人判断思考 · 非专业名词中文表达
支持日期参数用于回填历史日期
"""

import requests
import json
import sys
import os
import requests, time, re, json
from datetime import datetime, timedelta
from pathlib import Path

# ─── 新增模块 ───────────────────────────────────────────────
from scripts.llm_utils import extract_response
from scripts.summarize import gen_daily_summary, format_summary_markdown
from scripts.rank import rank_content

# ─── 配置 ───────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OUTPUT_DIR = Path(__file__).parent.parent / "daily"


# ─── 工具函数 ────────────────────────────────────────────
def _hdrs():
    h = {"Accept": "application/json", "User-Agent": "tech-news-digest/1.0"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


def make_date(date_str=None):
    """解析日期字符串或返回今天"""
    if date_str:
        return datetime.strptime(date_str, "%Y-%m-%d")
    return datetime.now()


def format_date(dt=None, fmt="%Y年%m月%d日"):
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def slug_date(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


# ─── LLM 个人判断 ────────────────────────────────────────
def gen_judgment(item: dict, category: str) -> str:
    """
    调用 LLM 生成个人判断思考
    category: "ai_news" | "github" | "stackoverflow"
    非专业名词用中文，简洁有力，2-4句话
    """
    if not OPENAI_API_KEY:
        return ""

    if category == "ai_news":
        user_prompt = f"{{\"title\": \"{item['title']}\", \"abstract\": \"{item.get('abstract', 'N/A')}\"}}\n输出 JSON：{{\"judgment\": \"中文点评，2-4句\"}}"
    elif category == "github":
        user_prompt = f"{{\"name\": \"{item['name']}\", \"description\": \"{item.get('description', 'N/A')}\", \"language\": \"{item.get('language', '-')}\", \"stars\": \"{item.get('stars', '-')}\"}}\n输出 JSON：{{\"judgment\": \"中文点评，2-4句\"}}"
    else:
        user_prompt = f"{{\"title\": \"{item['title']}\", \"tags\": {item.get('tags', [])}}}\n输出 JSON：{{\"judgment\": \"中文点评，2-4句\"}}"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Output only a JSON object, nothing else. Example: {\"judgment\": \"some text\"}"},
            {"role": "user", "content": f"{user_prompt}\nRespond ONLY with: {{\"judgment\": \"...\"}}"}
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }
    if "openrouter" in OPENAI_BASE_URL:
        payload["model"] = LLM_MODEL
    elif "groq" in OPENAI_BASE_URL:
        payload["model"] = "llama-3.1-8b-instant"

    try:
        resp = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"].get("content", "").strip()
        # 尝试 JSON 解析（支持去掉 markdown 代码块）
        try:
            raw = re.sub(r"^```(?:json)?\s*", "", raw).strip()
            raw = re.sub(r"\s*```$", "", raw).strip()
            parsed = json.loads(raw)
            answer = parsed.get("judgment", parsed.get("answer", parsed.get("summary", "")))
            if answer:
                return answer
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass
        # JSON 解析失败：检查是否被截断的 JSON（如 '{"judgment": "...' 只有开头）
        if raw.startswith("{") and ':' in raw and raw.count('"') < 6:
            # 尝试用正则从截断 JSON 中提取字段值
            m = re.search(r'"\w+"\s*:\s*"([^"]*)"', raw)
            if m:
                return m.group(1).strip()
        # 直接返回原始 content
        return raw.strip('"').strip("'").strip()
    except Exception as e:
        return f"（判断生成失败: {e}）"


def gen_all_judgments(ai_news, github_trending, stackoverflow, use_llm=True):
    """为所有内容生成个人判断（串行，避免 API 限流）"""
    if not use_llm or not OPENAI_API_KEY:
        return ai_news, github_trending, stackoverflow

    print("  🧠 正在生成 AI 论文个人判断...")
    for n in ai_news:
        n["judgment"] = gen_judgment(n, "ai_news")
        time.sleep(0.5)

    print("  🧠 正在生成 GitHub 项目个人判断...")
    for r in github_trending:
        r["judgment"] = gen_judgment(r, "github")
        time.sleep(0.5)

    print("  🧠 正在生成 StackOverflow 问题个人判断...")
    for q in stackoverflow:
        q["judgment"] = gen_judgment(q, "stackoverflow")
        time.sleep(0.5)

    return ai_news, github_trending, stackoverflow


# ─── 1. OpenAlex AI 论文 ─────────────────────────────────
def fetch_openalex_news(dt=None, limit=5):
    """
    通过 OpenAlex API 搜索 AI/ML 高影响力论文
    dt: datetime 对象，用于过滤近N天的论文
    """
    url = (
        "https://api.openalex.org/works"
        "?search=artificial intelligence,machine learning,large language model"
        "&filter=publication_year:2025|2026"
        "&sort=relevance_score:desc"
        f"&per_page={limit}"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"title": f"⚠️ 获取失败: {e}", "url": "#", "published": "-", "abstract": "暂无"}]

    news = []
    for item in data.get("results", []):
        title = item.get("title", "无标题")
        abs_short = item.get("abstract_inverted_index")
        if abs_short:
            max_pos = max(max(positions) for positions in abs_short.values())
            recon = ["" for _ in range(max_pos + 1)]
            for word, positions in abs_short.items():
                for pos in positions:
                    recon[pos] = word
            abstract = " ".join(recon)[:300] + "..."
        else:
            abstract = "无摘要"

        authors = item.get("authorships", [])
        author_str = ", ".join(
            a.get("author", {}).get("display_name", "Unknown")
            for a in authors[:2]
        )
        pub_date = item.get("publication_date", "Unknown")
        url2 = item.get("doi", "#")

        news.append({
            "title": title,
            "url": url2,
            "published": f"{pub_date} · {author_str}" if author_str else pub_date,
            "abstract": abstract,
        })
    return news


# ─── 2. GitHub 高星活跃项目 ───────────────────────────────
def fetch_github_trending(dt=None, language="", limit=10):
    """
    获取 GitHub 高星活跃项目
    dt: datetime（用于设置基准日期，默认7天前）
    """
    if dt is None:
        dt = datetime.now()
    week_ago = (dt - timedelta(days=7)).strftime("%Y-%m-%d")
    query = f"stars:>500 pushed:>{week_ago}"
    if language:
        query += f" language:{language}"

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit}
    try:
        resp = requests.get(url, params=params, headers=_hdrs(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"rank": 1, "name": f"⚠️ 获取失败: {e}", "url": "#",
                 "description": "", "language": "-", "stars": "-",
                 "forks": "-", "today_stars": "-"}]

    repos = []
    for i, repo in enumerate(data.get("items", []), 1):
        repos.append({
            "rank": i,
            "name": repo.get("full_name", "unknown"),
            "url": repo.get("html_url", "#"),
            "description": repo.get("description") or "暂无描述",
            "language": repo.get("language") or "—",
            "stars": f"{repo.get('stargazers_count', 0):,}",
            "forks": f"{repo.get('forks_count', 0):,}",
            "today_stars": "⭐+?",
        })
    return repos


# ─── 3. StackOverflow 热点 ───────────────────────────────
def fetch_stackoverflow(tags=None, limit=5):
    """获取 StackOverflow 热点问题"""
    url = "https://api.stackexchange.com/2.3/questions"
    params = {
        "order": "desc",
        "sort": "votes",
        "site": "stackoverflow",
        "pagesize": limit,
    }
    if tags:
        params["tagged"] = ";".join(tags)
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"title": f"⚠️ 获取失败: {e}", "link": "#",
                 "tags": [], "votes": 0, "answers": 0, "views": 0}]

    questions = []
    for q in data.get("items", []):
        questions.append({
            "title": q.get("title", "无标题"),
            "link": q.get("link", "#"),
            "tags": q.get("tags", []),
            "votes": f"{q.get('score', 0):,}",
            "answers": q.get("answer_count", 0),
            "views": f"{q.get('view_count', 0):,}",
        })
    return questions

# ─── 渲染 Markdown ───────────────────────────────────────
def render_template(context):
    lines = []
    lines.append(f"# 技术快讯 | {context['date']}")
    lines.append("")
    lines.append("> 每天自动生成 | 更新周期: 每日 10:00 (UTC+8)")
    lines.append("> 数据来源: OpenAlex · GitHub Trending · StackOverflow")
    lines.append("")
    lines.append("---")
    lines.append("")
    # ── A1: 每日摘要（如果有）──
    daily_summary = context.get("daily_summary", "")
    if daily_summary:
        lines.append(daily_summary)
        lines.append("")

    # ── AI 资讯 ──
    lines.append("## 🤖 AI 资讯")
    lines.append("")
    if context["ai_news"]:
        for n in context["ai_news"]:
            lines.append(f"### {n['title']}")
            lines.append(f"- **来源**: OpenAlex")
            lines.append(f"- **论文**: [{n['title']}]({n['url']})")
            lines.append(f"- **发表**: {n['published']}")
            lines.append(f"- **摘要**: {n['abstract']}")
            if n.get("judgment"):
                lines.append(f"- **💡 判断**: {n['judgment']}")
            lines.append("")
    else:
        lines.append("*今日暂无 AI 相关论文*")
        lines.append("")
    lines.append("---")
    lines.append("")

    # ── GitHub ──
    lines.append("## 🔥 GitHub 高星活跃项目")
    lines.append("")
    if context["github_trending"]:
        for r in context["github_trending"]:
            lines.append(f"### {r['rank']}. {r['name']}")
            if r["description"] and r["description"] != "暂无描述":
                lines.append(f">{r['description']}")
            lines.append(f"- **语言**: {r['language']} | **⭐**: {r['stars']} | **🔱**: {r['forks']}")
            lines.append(f"- **链接**: [GitHub]({r['url']})")
            if r.get("judgment"):
                lines.append(f"- **💡 判断**: {r['judgment']}")
            lines.append("")
    else:
        lines.append("*今日暂无热门项目*")
        lines.append("")
    lines.append("---")
    lines.append("")

    # ── StackOverflow ──
    lines.append("## 💬 StackOverflow 技术热点")
    lines.append("")
    if context["stackoverflow"]:
        for q in context["stackoverflow"]:
            lines.append(f"### {q['title']}")
            tag_html = " ".join(f"`{t}`" for t in q["tags"])
            lines.append(f"- **标签**: {tag_html}")
            lines.append(f"- **投票**: {q['votes']} | **回答**: {q['answers']} | **浏览**: {q['views']}")
            lines.append(f"- **链接**: [查看问题]({q['link']})")
            if q.get("judgment"):
                lines.append(f"- **💡 判断**: {q['judgment']}")
            lines.append("")
    else:
        lines.append("*今日暂无热点问题*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("> 📬 订阅此仓库: Watch → Releases only | 如需定制化需求 Open Issue")

    return "\n".join(lines)


# ─── 主流程 ───────────────────────────────────────────────
def main(date_str=None, use_llm=True, use_ranking=True, deliver_channels=None):
    """
    date_str: YYYY-MM-DD 格式，None 表示今天
    use_llm: 是否调用 LLM 生成判断
    use_ranking: 是否启用个性化排序（基于 preferences.yaml）
    deliver_channels: 分发渠道列表，None 则跳过分发
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dt = make_date(date_str)
    date_label = format_date(dt)
    slug = slug_date(dt)

    print(f"📡 正在采集数据...（日期: {date_label}）")
    print("  🤖 OpenAlex AI 论文...")
    ai_news = fetch_openalex_news(dt=dt, limit=8)

    print("  🔥 GitHub 高星活跃项目...")
    github_trending = fetch_github_trending(dt=dt, limit=12)

    print("  💬 StackOverflow 热点...")
    stackoverflow = fetch_stackoverflow(tags=["python", "javascript", "machine-learning"], limit=8)

    # ── B1/B2: 个性化排序 ──────────────────────────────────
    if use_ranking:
        print("  🎯 个性化排序中（读取 preferences.yaml）...")
        ai_news, github_trending, stackoverflow = rank_content(
            ai_news, github_trending, stackoverflow
        )

    # LLM 判断
    has_judgments = False
    if use_llm and OPENAI_API_KEY:
        print("  🧠 正在生成个人判断...")
        ai_news, github_trending, stackoverflow = gen_all_judgments(
            ai_news, github_trending, stackoverflow, use_llm=True
        )
        has_judgments = True
    else:
        if not use_llm:
            print("  ⏭️ 跳过 LLM 判断（use_llm=False）")
        elif not OPENAI_API_KEY:
            print("  ⏭️ 跳过 LLM 判断（未配置 OPENAI_API_KEY）")

    # ── A1: 每日摘要 ───────────────────────────────────────
    daily_summary = ""
    if use_llm and OPENAI_API_KEY:
        print("  📝 正在生成每日摘要...")
        raw_summary = gen_daily_summary(ai_news, github_trending, stackoverflow)
        daily_summary = format_summary_markdown(raw_summary)
        print(f"    摘要: {raw_summary[:50]}...")
    else:
        print("  ⏭️ 跳过每日摘要（use_llm=False 或未配置 OPENAI_API_KEY）")

    context = {
        "date": date_label,
        "ai_news": ai_news,
        "github_trending": github_trending,
        "stackoverflow": stackoverflow,
        "has_judgments": has_judgments,
        "daily_summary": daily_summary,
    }

    print("  📝 渲染 Markdown...")
    md_content = render_template(context)

    out_file = OUTPUT_DIR / f"{slug}.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # ── B3: 多渠道分发 ────────────────────────────────────
    if deliver_channels:
        print(f"  📬 开始分发到: {', '.join(deliver_channels)} ...")
        from deliver import deliver
        results = deliver(md_content, deliver_channels)
        for ch, ok in results.items():
            print(f"     {ch}: {'✅' if ok else '❌'}")

    print(f"\n✅ 生成完成: {out_file}")
    print(f"   - AI 资讯: {len(ai_news)} 条")
    print(f"   - GitHub: {len(github_trending)} 条")
    print(f"   - StackOverflow: {len(stackoverflow)} 条")
    print(f"   - LLM 判断: {'✅' if has_judgments else '❌'}")
    print(f"   - 每日摘要: {'✅' if daily_summary else '❌'}")
    return str(out_file)


if __name__ == "__main__":
    # 找出第一个非 flag 参数作为日期
    date_arg = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            date_arg = arg
            break

    use_llm = "--no-llm" not in sys.argv
    use_ranking = "--no-ranking" not in sys.argv

    # 解析 --deliver 参数
    deliver_channels = None
    trends_output = None
    for arg in sys.argv:
        if arg.startswith("--deliver="):
            deliver_channels = [ch.strip() for ch in arg.split("=", 1)[1].split(",") if ch.strip()]
        if arg.startswith("--trends"):
            # 解析 --trends=7 或 --trends
            n_str = arg.split("=", 1)[1] if "=" in arg else "7"
            trends_output = n_str if n_str else "7"

    main(date_str=date_arg, use_llm=use_llm, use_ranking=use_ranking, deliver_channels=deliver_channels)

    # ── A2: 趋势分析 ────────────────────────────────────────
    if trends_output:
        from analyze_trends import gen_weekly_trends
        n = int(trends_output) if trends_output.isdigit() else 7
        output_path = f"daily/trends-{datetime.now().strftime('%Y-%m-%d')}.md"
        md = gen_weekly_trends(n=n, output_path=output_path)
        print(f"\n📊 趋势分析已生成: {output_path}")
