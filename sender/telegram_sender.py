"""
텔레그램 초안 전송 모듈 - 3개 메시지 구조
"""
import os
import time
import requests
from datetime import datetime
from typing import List

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
MSG_LIMIT = 3800


def send_message(text: str) -> bool:
    text = text[:4000] if len(text) > 4000 else text
    resp = requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True},
        timeout=10,
    )
    ok = resp.status_code == 200
    if not ok:
        print(f"  ⚠️ 전송 실패: HTTP {resp.status_code} | {resp.text[:200]}")
    return ok


def send_long_text(text: str) -> None:
    if len(text) <= MSG_LIMIT:
        send_message(text)
        return
    chunks = []
    remaining = text
    while len(remaining) > MSG_LIMIT:
        split_at = remaining.rfind("\n\n", 0, MSG_LIMIT)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, MSG_LIMIT)
        if split_at == -1:
            split_at = MSG_LIMIT
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        prefix = f"({i}/{total})\n\n" if total > 1 else ""
        send_message(f"{prefix}{chunk}")
        time.sleep(0.5)


def send_blog_draft(
    title: str = "",
    subtitle: str = "",
    body: str = "",
    tags: List[str] = None,
    one_line_summary: str = "",
    action_points: List[str] = None,
) -> None:
    if tags is None:
        tags = []
    if action_points is None:
        action_points = []

    today = datetime.now().strftime("%Y.%m.%d")
    tags_str = " ".join([f"#{t}" for t in tags]) if tags else ""

    # 메시지 1: 헤더
    msg1 = f"📝 블로그 초안 | {today}\n\n💡 핵심: {one_line_summary or '요약 없음'}"
    if tags_str:
        msg1 += f"\n\n🏷️ {tags_str}"
    send_message(msg1)
    time.sleep(0.4)

    # 메시지 2: 본문
    header = ""
    if title:
        header += f"제목: {title}\n"
    if subtitle:
        header += f"부제목: {subtitle}\n"
    if header:
        header += "\n"
    send_long_text(header + body)
    time.sleep(0.4)

    # 메시지 3: 실천 포인트 + CTA
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]
    if action_points:
        lines += ["✅ 오늘의 실천 포인트", ""]
        for i, p in enumerate(action_points, 1):
            lines.append(f"{i}. {p}")
        lines.append("")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💬 내 상황에 어떻게 적용할지 궁금하신가요?",
        "👉 30초 무료 재무진단: https://jwfinancial.co.kr/",
    ]
    send_message("\n".join(lines))
    print("  ✓ 텔레그램 전송 완료 (3개 메시지)")
