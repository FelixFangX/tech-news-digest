#!/usr/bin/env python3
"""
A2: 趋势分析模块
扫描 daily/ 目录下过去 7 天的 .md 文件，识别：
  - rising:   本周出现频率上升的话题
  - stable:   持续热门话题（每天都有）
  - emerging:  单日新焦点（某天突然出现多个相关条目）
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# ─── 配置 ────────────────────────────────────────────────
DAILY_DIR = Path(__file__).parent.parent / "daily"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://minimax.a7m.com.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "MiniMax-M2.7-highspeed")

# ─── 解析每日文件 ─────────────────────────────────────────

def extract_section(text: str, heading: str) -> list[str]:
    """提取以 heading (e.g. '## 🤖 AI 资讯') 开头到下一个 ## 之间的内容行"""
    lines = text.split("\n")
    result = []
    in_section = False
    for line in lines:
        if re.match(rf"^##\s+{re.escape(heading)}", line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            result.append(line)
    return result


def parse_daily_file(path: Path) -> dict:
    """解析单日 md 文件，提取 AI/GitHub/SO 条目"""
    content = path.read_text(encoding="utf-8")

    # AI news: 以 ### 标题 + 论文 URL
    ai_lines = extract_section(content, "🤖 AI 资讯")
    ai_titles = []
    for line in ai_lines:
        m = re.match(r"^### (.+)", line)
        if m:
            ai_titles.append(m.group(1).strip())

    # GitHub: 从 URL 中提取 owner/repo 格式
    gh_lines = extract_section(content, "🔥 GitHub")
    gh_repos = []
    for line in gh_lines:
        m = re.search(r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)", line)
        if m:
            gh_repos.append(m.group(1))

    # SO: 从标签行提取 `tag` 格式 + 标题
    so_lines = extract_section(content, "💬 StackOverflow")
    so_tags = []
    so_titles = []
    for line in so_lines:
        tm = re.match(r"^### (.+)", line)
        if tm:
            so_titles.append(tm.group(1).strip())
        # 提取标签行中的技术标签
        tag_m = re.findall(r"`([a-zA-Z0-9_.#+-]+)`", line)
        so_tags.extend([t.lower() for t in tag_m if t.lower() not in ("javascript", "python", "java", "c++", "c", "go", "rust", "ruby", "php", "typescript", "swift", "kotlin", "scala", "r")])

    return {
        "date": path.stem,  # "2026-04-12"
        "ai_titles": ai_titles,
        "gh_repos": gh_repos,
        "so_tags": list(set(so_tags)),
        "so_titles": so_titles,
    }


def get_recent_days(n=7) -> list[Path]:
    """返回最近 n 天的 daily md 文件路径，按日期升序"""
    today = datetime.now().strftime("%Y-%m-%d")
    files = []
    for i in range(n):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        p = DAILY_DIR / f"{date}.md"
        if p.exists():
            files.append(p)
    return sorted(files)


# ─── 话题提取（基于关键词 + LLM 辅助） ─────────────────────

def extract_keywords_from_titles(titles: list[str]) -> list[str]:
    """从标题列表中提取关键技术关键词（规则方法）"""
    stopwords = {"the", "a", "an", "of", "for", "in", "on", "with", "to", "and", "or", "by",
                 "from", "using", "using", "based", "via", "using", "towards", "toward",
                 "new", "using", "novel", "approach", "method", "system", "framework",
                 "large", "small", "using"}
    keywords = []
    for title in titles:
        words = re.findall(r"[A-Z][a-z0-9]+|[A-Z]{2,}", title)
        for w in words:
            w_lower = w.lower()
            if w_lower not in stopwords and len(w_lower) > 2:
                keywords.append(w_lower)
    return keywords


def extract_ai_domains(ai_titles: list[str]) -> dict[str, int]:
    """从 AI 论文标题中提取领域分布"""
    domain_patterns = {
        "LLM/LM":      ["large language model", "llm", "language model", "gpt", "bert", "transformer"],
        "MLOps":       ["mlops", "llmops", "deployment", "production", "monitoring"],
        "Computer Vision": ["vision", "image", "cnn", "yolo", "segmentation", "detection"],
        "Privacy":     ["privacy", "unlearning", "federated", "secure", "confidential"],
        "Robotics":    ["robot", "autonomous", "drone", "reinforcement"],
        "Science/Engineering": ["smart grid", "civil engineering", "medical", "ct mri", "software defect"],
        "Education":   ["education", "learning", "teaching"],
        "Debiasing":   ["bias", "fairness", "debias"],
        "Audio/Speech": ["speech", "audio", "asr", "tts"],
    }
    counts = defaultdict(int)
    for title in ai_titles:
        t = title.lower()
        for domain, patterns in domain_patterns.items():
            if any(p in t for p in patterns):
                counts[domain] += 1
    return dict(counts)


def count_topic_frequency(days_data: list[dict], topic: str) -> list[int]:
    """返回该 topic 在每天的出现次数"""
    topic_lower = topic.lower()
    return [
        sum(1 for t in d["ai_titles"] + d["so_titles"]
            if topic_lower in t.lower())
        for d in days_data
    ]


# ─── LLM 趋势解读 ─────────────────────────────────────────

def gen_trend_commentary(trends: dict, days_data: list[dict]) -> str:
    """用 LLM 为趋势数据生成中文解读"""
    if not OPENAI_API_KEY:
        return ""

    # 构建上下文摘要
    ai_counts = [len(d["ai_titles"]) for d in days_data]
    gh_counts = [len(d["gh_repos"]) for d in days_data]
    dates = [d["date"] for d in days_data]

    prompt = f"""过去{dates[0]}～{dates[-1]}的技术趋势数据：

AI 论文每日数量：{ai_counts}
GitHub 热门每日数量：{gh_counts}

热门话题分类：
- 持续热门（stable）：{', '.join(trends.get('stable', [])[:5])}
- 上升趋势（rising）：{', '.join(trends.get('rising', [])[:5])}
- 新兴焦点（emerging）：{', '.join(trends.get('emerging', [])[:5])}

请用简洁的中文（3-5句）总结本周技术趋势的主要变化。"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Output only a JSON object, nothing else. Example: {\"commentary\": \"some text\"}"},
            {"role": "user", "content": f"{prompt}\nRespond ONLY with: {{\"commentary\": \"...\"}}"}
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }
    if "openrouter" in OPENAI_BASE_URL or "groq" in OPENAI_BASE_URL:
        payload["model"] = LLM_MODEL

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
        try:
            raw = re.sub(r"^```(?:json)?\s*", "", raw).strip()
            raw = re.sub(r"\s*```$", "", raw).strip()
            parsed = json.loads(raw)
            return parsed.get("commentary", "")
        except (json.JSONDecodeError, ValueError, AttributeError):
            if raw.startswith("{") and raw.count('"') < 10:
                m = re.search(r'"\w+"\s*:\s*"([^"]*)"', raw)
                if m:
                    return m.group(1).strip()
            return raw.strip('"').strip("'").strip()
    except Exception:
        return ""


# ─── 核心趋势分析 ─────────────────────────────────────────

def analyze_trends(days_data: list[dict]) -> dict:
    """分析每天的数据，输出 rising/stable/emerging 分类"""
    # 收集所有话题及其每日出现天数
    topic_days = defaultdict(list)  # topic -> [(date, count)]
    all_domains = defaultdict(int)  # domain -> total_count

    for day in days_data:
        domains = extract_ai_domains(day["ai_titles"])
        for domain, cnt in domains.items():
            all_domains[domain] += cnt
            topic_days[domain].append((day["date"], cnt))

        # GitHub repos 简化
        for repo in day["gh_repos"]:
            topic_days[repo].append((day["date"], 1))

        # SO 技术标签
        for tag in day.get("so_tags", []):
            topic_days[tag].append((day["date"], 1))

    # 计算每个话题的趋势
    rising, stable, emerging = [], [], []
    half = len(days_data) // 2

    for topic, day_counts in topic_days.items():
        if len(day_counts) < 1:
            continue
        total = sum(c for _, c in day_counts)
        if total < 2:
            continue  # 出现次数太少，跳过

        # 统计出现在多少天
        days_seen = len(day_counts)

        # 前后半段对比（判断是否上升）
        if half >= 2 and days_seen >= 3:
            first_half = sum(c for d, c in day_counts if d <= days_data[half - 1]["date"])
            second_half = sum(c for d, c in day_counts if d > days_data[half - 1]["date"])
            if second_half > first_half * 1.5:
                rising.append(topic)
                continue

        if days_seen >= len(days_data) * 0.6:
            stable.append(topic)
        elif days_seen == 1 and total >= 2:
            emerging.append(topic)

    # 排序：stable/rising 按频率，emerging 按单日集中度
    rising.sort(key=lambda t: sum(c for d, c in topic_days[t]), reverse=True)
    stable.sort(key=lambda t: sum(c for d, c in topic_days[t]), reverse=True)
    emerging.sort(key=lambda t: sum(c for d, c in topic_days[t]), reverse=True)

    return {
        "rising":   rising[:8],
        "stable":  stable[:8],
        "emerging": emerging[:5],
    }


# ─── 输出格式 ─────────────────────────────────────────────

def format_trends_markdown(trends: dict, commentary: str, dates: list[str]) -> str:
    """将趋势数据格式化为 markdown 报告"""
    lines = [
        "# 📊 技术趋势周报",
        f"_{dates[0]} ～ {dates[-1]}_",
        "",
    ]
    if commentary:
        lines.extend([f"> {commentary}", ""])

    if trends["stable"]:
        lines.append("### 🔍 持续热门（Stable）")
        for t in trends["stable"]:
            lines.append(f"- **{t}**")
        lines.append("")

    if trends["rising"]:
        lines.append("### 📈 上升趋势（Rising）")
        for t in trends["rising"]:
            lines.append(f"- **{t}**")
        lines.append("")

    if trends["emerging"]:
        lines.append("### ⚡ 新兴焦点（Emerging）")
        for t in trends["emerging"]:
            lines.append(f"- **{t}**")
        lines.append("")

    return "\n".join(lines)


# ─── 主入口 ───────────────────────────────────────────────

def gen_weekly_trends(n=7, output_path=None) -> str:
    """
    生成过去 n 天的趋势报告。
    若 output_path 指定，则写入文件；返回 markdown 内容。
    """
    recent = get_recent_days(n)
    if not recent:
        return "（无数据）"

    days_data = [parse_daily_file(p) for p in recent]
    trends = analyze_trends(days_data)
    dates = [d["date"] for d in days_data]
    commentary = gen_trend_commentary(trends, days_data)
    md = format_trends_markdown(trends, commentary, dates)

    if output_path:
        Path(output_path).write_text(md, encoding="utf-8")

    return md


if __name__ == "__main__":
    md = gen_weekly_trends(n=7)
    print(md)
