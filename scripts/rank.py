#!/usr/bin/env python3
"""
B1 + B2: 个性化推荐与排序
基于用户兴趣配置，对采集的原始内容做过滤 + 重排序
"""

import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


def load_preferences(config_path: Optional[str] = None) -> dict:
    """加载用户偏好配置"""
    if config_path is None:
        config_path = os.getenv("PREFERENCES_PATH", str(Path(__file__).parent.parent / "preferences.yaml"))

    p = Path(config_path)
    if not p.exists():
        return {"interests": [], "exclude": [], "fetch": {"max_per_category": 0}}

    with open(p, encoding="utf-8") as f:
        raw = f.read()

    # 替换环境变量占位符
    for key, val in os.environ.items():
        raw = raw.replace(f"${{{key}}}", val)

    return yaml.safe_load(raw)


def match_score(item: dict, interests: List[str], category: str) -> float:
    """
    计算单条内容与用户兴趣的匹配得分
    category: "ai_news" | "github" | "stackoverflow"
    """
    if not interests:
        return 1.0  # 无偏好配置时全部返回 1.0（不排序）

    score = 0.0
    texts = []

    if category == "ai_news":
        texts = [
            item.get("title", ""),
            item.get("abstract", ""),
        ]
    elif category == "github":
        texts = [
            item.get("name", ""),
            item.get("description", ""),
        ]
    elif category == "stackoverflow":
        texts = [
            item.get("title", ""),
            " ".join(item.get("tags", [])),
        ]

    combined = " ".join(texts).lower()
    for interest in interests:
        # 支持完整匹配和词根匹配
        if interest.lower() in combined:
            score += 1.0
        # 检查 interest 中是否有空格（短语匹配）
        if " " in interest and interest.lower() in combined:
            score += 0.5

    return score


def filter_items(items: List[dict], interests: List[str], exclude: List[str], category: str) -> List[dict]:
    """过滤 + 打分 + 排序"""
    if not items:
        return items

    # 过滤排除词
    filtered = []
    for item in items:
        texts = []
        if category == "ai_news":
            texts = [item.get("title", ""), item.get("abstract", "")]
        elif category == "github":
            texts = [item.get("name", ""), item.get("description", "")]
        elif category == "stackoverflow":
            texts = [item.get("title", ""), " ".join(item.get("tags", []))]

        combined = " ".join(texts).lower()
        if any(ex.lower() in combined for ex in exclude):
            continue
        filtered.append(item)

    # 计算兴趣匹配得分
    for item in filtered:
        item["_interest_score"] = match_score(item, interests, category)

    # 按得分降序，保留原始顺序作为 tiebreaker
    return sorted(filtered, key=lambda x: (x.get("_interest_score", 0), 0), reverse=True)


def rank_content(
    ai_news: List[dict],
    github_trending: List[dict],
    stackoverflow: List[dict],
    config_path: Optional[str] = None,
) -> tuple[List[dict], List[dict], List[dict]]:
    """
    整合入口：对三类内容执行过滤 + 排序
    返回 (ranked_ai_news, ranked_github, ranked_stackoverflow)
    """
    prefs = load_preferences(config_path)
    interests = prefs.get("interests", [])
    exclude = prefs.get("exclude", [])
    max_per = prefs.get("fetch", {}).get("max_per_category", 0)

    ranked_ai = filter_items(ai_news, interests, exclude, "ai_news")
    ranked_gh = filter_items(github_trending, interests, exclude, "github")
    ranked_so = filter_items(stackoverflow, interests, exclude, "stackoverflow")

    if max_per > 0:
        ranked_ai = ranked_ai[:max_per]
        ranked_gh = ranked_gh[:max_per]
        ranked_so = ranked_so[:max_per]

    return ranked_ai, ranked_gh, ranked_so


def format_ranking_debug(
    ai_news: List[dict],
    github_trending: List[dict],
    stackoverflow: List[dict],
) -> str:
    """输出调试信息（哪些条被排序到了前面，为什么）"""
    lines = ["## 🔍 排序调试信息", ""]
    prefs = load_preferences(config_path=None)
    interests = prefs.get("interests", [])

    if not interests:
        return ""

    lines.append(f"**兴趣关键词**: {', '.join(interests)}")
    lines.append("")

    for cat, items, label in [
        (ai_news, "ai_news", "AI 论文"),
        (github_trending, "github", "GitHub 项目"),
        (stackoverflow, "stackoverflow", "SO 问题"),
    ]:
        if not items:
            continue
        lines.append(f"### {label}")
        for i, item in enumerate(items[:3], 1):
            score = item.get("_interest_score", 0)
            title = item.get("title", "") or item.get("name", "") or item.get("title", "")
            lines.append(f"{i}. [{title[:50]}]({item.get('url', item.get('link', '#'))}) (匹配得分: {score})")
        lines.append("")

    return "\n".join(lines)
