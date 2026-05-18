"""
텔레그램 초안 전송 모듈
- 3개 메시지로 압축 전송
  메시지1: 헤더 (핵심 요약 + 태그)
  메시지2: 본문 (제목 + 내용, 길면 자동 분할)
  메시지3: 실천 포인트 + CTA
- parse_mode 없음: 특수문자 오류 방지
"""
import os
import time
import requests
import tempfile
from datetime import datetime
from typing import List

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
MSG_LIMIT = 3800


def send_message(text: str) -> bool:
    """plain text 메시지 전송 (parse_mode 없음)"""
    text = text[:4000] if len(text) > 4000 else text
    resp = requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
    ok = resp.status_code == 200
    if not ok:
        print(f"  ⚠️ 전송 실패: HTTP {resp.status_code} | {resp.text[:200]}")
    return ok


def send_long_text(text: str, label: str = "") -> None:
    """
    3800자 초과 텍스트를 단락 경계에서 분할 전송.
    분할이 필요 없으면 단일 메시지로 전송.
    """
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
    """
    블로그 초안을 3개 메시지로 전송

    메시지 1: 헤더 (날짜 + 핵심 요약 + 태그)
    메시지 2: 본문 (제목 + 부제목 + 내용)
    메시지 3: 실천 포인트 + CTA
    """
    if tags is None:
        tags = []
    if action_points is None:
        action_points = []

    today = datetime.now().strftime("%Y.%m.%d")
    tags_str = " ".join([f"#{t}" for t in tags]) if tags else ""

    # ── 메시지 1: 헤더 ────────────────────────────────────────
    msg1_lines = [
        f"📝 블로그 초안 | {today}",
        "",
        f"💡 핵심: {one_line_summary}" if one_line_summary else "💡 핵심 요약 없음",
    ]
    if tags_str:
        msg1_lines += ["", f"🏷️ {tags_str}"]

    send_message("\n".join(msg1_lines))
    time.sleep(0.4)

    # ── 메시지 2: 본문 ────────────────────────────────────────
    body_header = []
    if title:
        body_header.append(f"제목: {title}")
    if subtitle:
        body_header.append(f"부제목: {subtitle}")
    if body_header:
        body_header.append("")

    full_body = "\n".join(body_header) + body
    send_long_text(full_body)
    time.sleep(0.4)

    # ── 메시지 3: 실천 포인트 + CTA ───────────────────────────
    msg3_lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]

    if action_points:
        msg3_lines += ["✅ 오늘의 실천 포인트", ""]
        for i, point in enumerate(action_points, 1):
            msg3_lines.append(f"{i}. {point}")
        msg3_lines.append("")

    msg3_lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💬 내 상황에 어떻게 적용할지 궁금하신가요?",
        "👉 30초 무료 재무진단: https://jwfinancial.co.kr/",
    ]

    send_message("\n".join(msg3_lines))
    print(f"  ✓ 텔레그램 전송 완료 (3개 메시지)")


if __name__ == "__main__":
    send_blog_draft(
        title="규제도 못 막은 주담대 5.5조 폭증",
        subtitle="2026년 5월 18일 경제 브리핑 | JW파이낸셜",
        body="테스트 본문입니다.\n\n내용이 길게 이어집니다.",
        tags=["주담대", "금리인하", "부동산대출", "가계부채"],
        one_line_summary="규제 강화에도 주담대 8개월 최대 급증",
        action_points=[
            "현재 주담대 변동금리 확인 후 고정금리 전환 시뮬레이션 (1억 기준 연 50만원 차이)",
            "5년 내 갱신 예정 대출 있다면 금융기관 상담으로 우대금리 협상 (0.1~0.2% 우대 가능)",
        ],
    )
