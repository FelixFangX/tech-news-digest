"""
统一 LLM 响应解析工具
兼容所有 OpenAI / Anthropic 兼容协议模型：
  - 标准模型（GPT-4o, GPT-4o-mini, Claude 等）：回复在 content
  - 推理模型（MiniMax M2, DeepSeek R1 等）：思考在 reasoning_content，回复在 content
  - 部分推理模型：actual response 在 reasoning_content 最后一段

策略：content 优先 → looks_complete 启发式判断 → 不完整则从 reasoning_content 提取
"""

import re


def looks_complete(text: str) -> bool:
    """启发式判断 content 是否为完整回复（非截断/非引导语）"""
    if not text or len(text) < 8:
        return False

    # 疑似不完整的结尾（句中被截断）
    if text[-1] in "。，、；，「":
        return False

    # 疑似未遵从不推理指令的引导语前缀
    forbidden_prefixes = [
        "我来", "Let me", "I will", "首先", "以下", "这篇",
        "我需要", "注意：", "直接输出", "我先", "先说",
        "判断：", "好的，", "好的", "我认为", "输出判断",
        "点评：", "点评要点", "判断要点", "评论：",
        "这句", "这段", "这样", "以下判断",
        "让我", "让我数", "让我写", "我来写",
        "- ", "* ", "1. ", "2. ", "3. ",  # 列表前缀
    ]
    for p in forbidden_prefixes:
        if text.startswith(p):
            return False

    # 引导语检测（模型还在说话，还没到正文）
    lead_ins = ["这篇", "这个", "首先", "接下来", "下面"]
    for lead in lead_ins:
        if text.startswith(lead) and len(text) < 30:
            return False

    return True


def extract_response(msg: dict) -> str:
    """
    从 LLM response message 中提取实际回复内容。
    兼容所有 OpenAI / Anthropic 兼容协议模型：
      - 标准模型（GPT-4o, GPT-4o-mini, Claude 等）：回复在 content
      - 推理模型（MiniMax M2, DeepSeek R1 等）：思考在 reasoning_content，回复在 content
      - 部分推理模型：actual response 在 reasoning_content 最后一段

    策略：content 优先 → looks_complete 启发式判断 → 不完整则从 reasoning_content 提取最后一段
    但如果 reasoning_content 比 content 还短（或内容模式相同），优先信任 content
    """
    raw_content = msg.get("content", "").strip()
    raw_reasoning = msg.get("reasoning_content", "").strip()

    def is_meta_commentary(text: str) -> bool:
        """检测是否为描述任务本身的元评论（而非实际回复）"""
        if not text or len(text) < 5:
            return True
        meta_patterns = [
            "让我数一下", "我来数", "字数统计", "符合要求", "完美",
            "好的", "我先", "首先", "以下",
        ]
        return any(text.startswith(p) for p in meta_patterns)

    # 策略：优先信任 content，除非它是元评论
    if looks_complete(raw_content) and not is_meta_commentary(raw_content):
        # content 看起来是正常回复
        answer = raw_content
    elif raw_reasoning:
        # content 是元评论或不完整 → 从 reasoning_content 提取最后一段
        paragraphs = raw_reasoning.split("\n\n")
        if paragraphs:
            # 找最后一个长度 >= 15 的段落（实际回复，而非截断碎片）
            candidate = ""
            for para in reversed(paragraphs):
                para = para.strip()
                if len(para) >= 15:
                    candidate = para
                    break
            answer = candidate if candidate else raw_content
        else:
            answer = raw_content
    else:
        answer = raw_content

    # 清理首尾引号和空白
    return answer.strip('"').strip("'").strip()
