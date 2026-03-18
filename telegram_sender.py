"""
텔레그램 초안 전송 모듈
- 섹션 인식 분할: 실천 포인트·핵심 요약이 잘리지 않도록 보장
- 실천 포인트 / 핵심 한 줄 요약은 별도 메시지로 항상 전송
"""
import os
import time
import requests
import tempfile
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# 텔레그램 단일 메시지 안전 한도
MSG_LIMIT = 3800


def send_message(text: str) -> bool:
    """텍스트 메시지 전송 (4096자 이내)"""
    resp = requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
    ok = resp.status_code == 200
    if not ok:
        print(f"  ⚠️ 메시지 전송 실패: {resp.status_code} {resp.text[:200]}")
    return ok


def send_document(content: str, filename: str) -> bool:
    """파일로 전송 (긴 초안용)"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name

    with open(tmp_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": f"📄 {filename}"},
            files={"document": (filename, f, "text/plain")},
            timeout=15,
        )
    os.unlink(tmp_path)
    return resp.status_code == 200


# ── 섹션 경계 마커 (이 위치에서 분할 선호) ──────────────────────
# 우선순위 높은 순서대로
SECTION_MARKERS = [
    "\n\n━━",          # 구분선
    "\n\n【",          # 블록 헤더
    "\n\n## ",         # 마크다운 h2
    "\n\n━━ ",         # 변환된 h2
    "\n\n▶ ",          # 변환된 h3
    "\n\n◆ ",          # 변환된 h1
    "\n\n✅",          # 실천 포인트 항목
    "\n\n💬",          # CTA
    "\n\n",            # 일반 단락
    "\n",              # 줄바꿈
]

# 절대 잘리면 안 되는 섹션 식별 키워드
PROTECTED_SECTIONS = [
    "실천 포인트",
    "오늘의 실천",
    "핵심 한 줄 요약",
    "한 줄 요약",
    "【태그】",
    "【핵심",
    "💬",              # CTA
    "👉 무료 상담",
]


def _find_best_split(text: str, limit: int) -> int:
    """
    limit 이내에서 가장 좋은 분할 위치를 찾는다.
    섹션 경계를 우선하되, 보호 섹션이 분할되지 않도록 한다.
    """
    if len(text) <= limit:
        return len(text)

    # 보호 섹션이 limit 이내에서 시작되는지 확인
    # → 보호 섹션 직전에서 자른다
    for keyword in PROTECTED_SECTIONS:
        pos = text.find(keyword, 1)  # 맨 앞은 제외
        if 0 < pos <= limit:
            # 이 섹션이 잘릴 수 있으므로 그 직전(직전 단락 경계)에서 자르기
            before = text.rfind("\n\n", 0, pos)
            if before > 0:
                return before
            # 단락 경계가 없으면 줄바꿈에서
            before = text.rfind("\n", 0, pos)
            if before > 0:
                return before

    # 섹션 마커 기준으로 분할 (우선순위 순)
    for marker in SECTION_MARKERS:
        pos = text.rfind(marker, 0, limit)
        if pos > limit // 2:  # 너무 앞에서 자르지 않기
            return pos + len(marker)

    # 최후 수단: limit에서 강제 분할
    return limit


def send_long_text(text: str) -> None:
    """
    섹션 인식 분할 전송.
    보호 섹션(실천 포인트, 요약 등)이 메시지 경계에서 잘리지 않도록 보장.
    """
    chunks = []
    remaining = text

    while len(remaining) > MSG_LIMIT:
        split_at = _find_best_split(remaining, MSG_LIMIT)
        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)

    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        prefix = f"📄 <b>({i}/{total})</b>\n\n" if total > 1 else ""
        send_message(f"{prefix}{chunk}")
        time.sleep(0.5)


def send_blog_draft(
    draft_text: str,
    one_line_summary: str = "",
    action_points: str = "",
) -> None:
    """
    블로그 초안 텔레그램 전송.

    순서:
    1. 헤더 메시지 (핵심 요약 포함)
    2. 본문 분할 전송
    3. 실천 포인트 별도 메시지 (보장 전송)
    4. 핵심 한 줄 요약 별도 메시지 (보장 전송)
    """
    today = datetime.now().strftime("%Y.%m.%d")

    # ── 1. 헤더 ───────────────────────────────────────────────
    header = (
        f"📝 <b>블로그 초안 생성 완료</b> ({today})\n\n"
        f"💡 {one_line_summary}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    send_message(header)
    time.sleep(0.3)

    # ── 2. 본문 분할 전송 ─────────────────────────────────────
    send_long_text(draft_text)
    time.sleep(0.5)

    # ── 3. 실천 포인트 보장 전송 ──────────────────────────────
    if action_points and action_points.strip():
        ap_msg = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ <b>[오늘의 실천 포인트 — 별도 전송]</b>\n\n"
            f"{action_points.strip()}"
        )
        send_message(ap_msg)
        time.sleep(0.3)
    else:
        # action_points가 없을 때: 본문에서 자동 탐색해서 재전송
        _try_resend_action_points(draft_text)
        time.sleep(0.3)

    # ── 4. 핵심 한 줄 요약 보장 전송 ─────────────────────────
    if one_line_summary and one_line_summary.strip():
        summary_msg = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>[핵심 한 줄 요약 — 별도 전송]</b>\n\n"
            f"{one_line_summary.strip()}"
        )
        send_message(summary_msg)

    print(f"  ✓ 텔레그램 전송 완료 (헤더 + 본문 + 실천포인트 + 요약 보장)")


def _try_resend_action_points(draft_text: str) -> None:
    """
    draft_text(포맷된 본문)에서 실천 포인트 섹션을 재탐색해서 전송.
    action_points 필드가 비어 있을 때 폴백으로 사용.
    """
    markers = ["━━ 오늘의 실천 포인트", "오늘의 실천 포인트", "실천 포인트", "▶ 실천"]
    for marker in markers:
        idx = draft_text.find(marker)
        if idx != -1:
            section = draft_text[idx:]
            # CTA 또는 다음 섹션에서 자르기
            for end_marker in ["💬", "【태그】", "━━━━━━━━━━━━━━━━━━━━━━━━━"]:
                end = section.find(end_marker, len(marker))
                if end != -1:
                    section = section[:end].strip()
                    break
            if section.strip():
                msg = (
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "✅ <b>[오늘의 실천 포인트 — 별도 전송]</b>\n\n"
                    f"{section.strip()}"
                )
                send_message(msg)
            return


if __name__ == "__main__":
    send_blog_draft(
        draft_text="테스트 초안입니다.\n\n## 오늘의 실천 포인트\n✅ 실천 1: 예금금리 확인\n✅ 실천 2: ETF 비중 점검",
        one_line_summary="오늘의 경제 한 줄 요약 테스트",
        action_points="## 오늘의 실천 포인트\n✅ 실천 1: 예금금리 확인\n✅ 실천 2: ETF 비중 점검",
    )
