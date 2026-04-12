#!/usr/bin/env python3
"""
B3: 多渠道分发
支持 Telegram Bot / Email / WeChat (ilink)
"""

import os
import re
import smtplib
import requests
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

# ─── 加载 preferences.yaml ────────────────────────────────
def _load_preferences():
    """加载 preferences.yaml（env vars 优先）"""
    cfg = {}
    pref_file = Path(__file__).parent.parent / "preferences.yaml"
    if pref_file.exists():
        try:
            import yaml
            with open(pref_file, encoding="utf-8") as f:
                raw = f.read()
            # 替换 ${ENV_VAR} 形式的环境变量
            def repl(m):
                return os.getenv(m.group(1), "")
            raw = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, raw)
            raw = re.sub(r"#.*", "", raw)  # 去掉注释行
            data = yaml.safe_load(raw)
            if data:
                cfg = data
        except Exception:
            pass
    return cfg

PREF = _load_preferences()


# ─── Telegram ────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", PREF.get("delivery", {}).get("telegram_bot_token", ""))
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", PREF.get("delivery", {}).get("telegram_chat_id", ""))


def send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    """通过 Telegram Bot 发送消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⏭️ Telegram 未配置（TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未设置）")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print(f"  ✅ Telegram 发送成功")
        return True
    except Exception as e:
        print(f"  ❌ Telegram 发送失败: {e}")
        return False


def md_to_telegram(text: str) -> str:
    """
    将 Markdown 转换为 Telegram 支持的格式
    - Bold: **text** → *text*
    - Code: `code` → ```code```
    - Links: [text](url) → [text](url) (Telegram 兼容)
    """
    import re
    # Bold: **text** → *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    # Inline code: `code` 保持不变（Telegram 支持）
    # Remove excess newlines (Telegram prefers compact)
    text = text.strip()
    return text


# ─── Email ────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", PREF.get("delivery", {}).get("smtp_host", ""))
SMTP_PORT = int(os.getenv("SMTP_PORT", str(PREF.get("delivery", {}).get("smtp_port", 587))))
SMTP_USER = os.getenv("SMTP_USER", PREF.get("delivery", {}).get("smtp_user", ""))
SMTP_PASS = os.getenv("SMTP_PASS", PREF.get("delivery", {}).get("smtp_pass", ""))
EMAIL_TO = os.getenv("EMAIL_TO", ",".join(PREF.get("delivery", {}).get("email_to", [])))
EMAIL_FROM = os.getenv("EMAIL_FROM", PREF.get("delivery", {}).get("email_from", SMTP_USER))


def send_email(subject: str, html_body: str, text_body: str = "") -> bool:
    """通过 SMTP 发送邮件"""
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        print("  ⏭️ Email 未配置（SMTP 相关环境变量未设置）")
        return False

    if not EMAIL_TO or EMAIL_TO == [""]:
        print("  ⏭️ Email 未配置收件人（EMAIL_TO 未设置）")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(f"  ✅ Email 发送成功 -> {', '.join(EMAIL_TO)}")
        return True
    except Exception as e:
        print(f"  ❌ Email 发送失败: {e}")
        return False


def md_to_html(md_text: str) -> str:
    """简易 Markdown → HTML 转换（用于 Email）"""
    import re
    html = md_text
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    # Code blocks
    html = re.sub(r'```(\w*)\n(.+?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    # Blockquotes
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    # HR
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    # Line breaks
    html = html.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<html><body><p>{html}</p></body></html>"


# ─── WeChat (ilink) ──────────────────────────────────────────
# 复用 research-thinking-ai 中已有的 WeChat ilink 基础设施
# 通过环境变量 WEIXIN_ILINK_HOOK 指定发送端点
WEIXIN_ILINK_HOOK = os.getenv("WEIXIN_ILINK_HOOK", PREF.get("delivery", {}).get("wechat_ilink_hook", ""))


def send_wechat(text: str) -> bool:
    """通过微信 ilink 协议发送文本消息"""
    if not WEIXIN_ILINK_HOOK:
        print("  ⏭️ WeChat 未配置（WEIXIN_ILINK_HOOK 未设置）")
        return False

    try:
        resp = requests.post(
            WEIXIN_ILINK_HOOK,
            json={"content": text},
            timeout=10,
        )
        resp.raise_for_status()
        print(f"  ✅ WeChat 发送成功")
        return True
    except Exception as e:
        print(f"  ❌ WeChat 发送失败: {e}")
        return False


# ─── 主分发入口 ──────────────────────────────────────────────
def deliver(content: str, channels: Optional[List[str]] = None) -> dict:
    """
    将快讯内容通过多渠道分发
    channels: ["telegram", "email", "wechat"] 或 None（全部）
    返回各渠道发送结果
    """
    if channels is None:
        channels = ["telegram", "email", "wechat"]

    results = {}

    if "telegram" in channels:
        tg_text = md_to_telegram(content)
        # Telegram 消息有 4096 字符限制，截断
        if len(tg_text) > 4000:
            tg_text = tg_text[:4000] + "\n\n...（内容过长，已截断）"
        results["telegram"] = send_telegram(tg_text)

    if "email" in channels:
        subject = "📡 技术快讯 " + content.split("\n")[0].replace("# ", "").strip()
        html_body = md_to_html(content)
        text_body = content  # 纯文本降级
        results["email"] = send_email(subject, html_body, text_body)

    if "wechat" in channels:
        # 微信消息需要精简，只发摘要部分
        import re
        summary_match = re.search(r'> \*\*今日要点\*\* (.+?)。?\n', content)
        if summary_match:
            wc_text = f"📡 技术快讯\n\n{summary_match.group(1)}。\n\n完整版: github.com/ColeFang/tech-news-digest"
        else:
            wc_text = content[:500] + "\n\n完整版: github.com/ColeFang/tech-news-digest"
        results["wechat"] = send_wechat(wc_text)

    return results
