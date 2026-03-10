"""
텔레그램 초안 전송 모듈
- 4096자 초과 시 파일(.txt)로 전송
- 기존 Telegram 봇 토큰/채팅 ID 재사용
"""
import os
import requests
import tempfile
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


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
    return resp.status_code == 200


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


def send_blog_draft(draft_text: str, one_line_summary: str = "") -> None:
    """블로그 초안 텔레그램 전송"""
    today = datetime.now().strftime("%Y.%m.%d")
    filename = f"blog_draft_{today}.txt"

    # 헤더 메시지 (짧게)
    header = (
        f"📝 <b>블로그 초안 생성 완료</b> ({today})\n\n"
        f"💡 {one_line_summary}\n\n"
        f"아래 파일을 열어 검토 후 네이버 블로그에 복붙하세요."
    )

    send_message(header)

    # 초안 본문은 파일로
    if len(draft_text) > 4000:
        send_document(draft_text, filename)
    else:
        send_message(f"<pre>{draft_text[:4000]}</pre>")

    print(f"  ✓ 텔레그램 전송 완료")


if __name__ == "__main__":
    send_blog_draft("테스트 초안입니다.", "오늘의 경제 한 줄 요약 테스트")
