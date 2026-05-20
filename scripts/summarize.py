#!/usr/bin/env python3
"""
A1: 每日摘要生成器
在每份快讯开头，由 LLM 生成一段今日技术形势综述（3-5 句话）
兼容所有 OpenAI 兼容协议的 LLM API。
"""

import os
import re
import json
import requests
from typing import List, Dict

# 统一 LLM 配置（OpenAI 兼容协议）
LLM_API_KEY = (
    os.getenv("LLM_API_KEY")
    or os.getenv("MINIMAX_API_KEY")
    or os.getenv("OPENAI_API_KEY", "")
)
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("MINIMAX_BASE_URL")
    or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# 向后兼容
MINIMAX_API_KEY = LLM_API_KEY
MINIMAX_BASE_URL = LLM_BASE_URL
MINIMAX_MODEL = LLM_MODEL


def build_summary_prompt(ai_news: List[dict], github_trending: List[dict], stackoverflow: List[dict]) -> str:
    """构建摘要 prompt，将所有内容浓缩为参考上下文"""

    # 提取 AI 论文标题（截断到 60 字符避免 prompt 过长）
    ai_titles = "；".join(n.get("title", "")[:60] for n in ai_news[:5]) or "无"

    # 提取 GitHub 项目名 + 描述
    gh_items = []
    for r in github_trending[:8]:
        name = r.get("name", "")
        desc = r.get("description", "")[:60]
        gh_items.append(f"{name}: {desc}")
    gh_text = "；".join(gh_items) or "无"

    # 提取 SO 问题标题（截断到 60 字符）
    so_titles = "；".join(q.get("title", "")[:60] for q in stackoverflow[:5]) or "无"

    prompt = f"今日内容：\n\n【AI论文】{ai_titles}\n【GitHub】{gh_text}\n【SO】{so_titles}"
    return prompt


def gen_daily_summary(ai_news: List[dict], github_trending: List[dict], stackoverflow: List[dict]) -> str:
    """调用 LLM 生成每日摘要（OpenAI 兼容协议）"""
    if not LLM_API_KEY:
        return "（未配置 LLM_API_KEY，跳过摘要）"

    from scripts.llm_utils import extract_response

    prompt = build_summary_prompt(ai_news, github_trending, stackoverflow)

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Output only a JSON object. No markdown fences, no explanation."
            },
            {
                "role": "user",
                "content": f"{prompt}\nRespond ONLY with: {{\"summary\": \"中文导语\"}}"
            }
        ],
        "max_tokens": 2048,
        "temperature": 0.7,
    }

    try:
        resp = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        finish_reason = data["choices"][0].get("finish_reason", "")
        msg = data["choices"][0]["message"]
        raw = extract_response(msg)
        if finish_reason == "length" or not raw:
            payload["max_tokens"] = 4096
            resp2 = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json=payload, timeout=30,
            )
            resp2.raise_for_status()
            data2 = resp2.json()
            raw = extract_response(data2["choices"][0]["message"])
        try:
            raw = re.sub(r"^```(?:json)?\s*", "", raw).strip()
            raw = re.sub(r"\s*```$", "", raw).strip()
            parsed = json.loads(raw)
            answer = parsed.get("summary", parsed.get("content", ""))
            if answer:
                return answer
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass
        if raw.startswith("{") and ':' in raw and raw.count('"') < 6:
            m = re.search(r'"\w+"\s*:\s*"([^"]*)"', raw)
            if m:
                return m.group(1).strip()
        return raw.strip('"').strip("'").strip()
    except Exception as e:
        return f"（摘要生成失败: {e}）"


def format_summary_markdown(summary: str) -> str:
    """将摘要格式化为 Markdown 片段"""
    if not summary or summary.startswith("（"):
        return ""
    return f"""> **今日要点** {summary}\n\n---"""
