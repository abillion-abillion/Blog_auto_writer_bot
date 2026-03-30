"""
블로그 봇 메인 실행 파일
실행: python blog_draft.py
"""
import sys
import os
import inspect

# 경로 설정
sys.path.insert(0, os.path.dirname(__file__))

from sources.rss_collector import collect_all_news, select_top_articles
from generator.claude_writer import generate_blog_draft, format_for_naver_blog
from sender.telegram_sender import send_blog_draft

# 신버전 여부: action_points 파라미터 존재 확인
_SENDER_HAS_ACTION_POINTS = "action_points" in inspect.signature(send_blog_draft).parameters


def _append_guaranteed_sections(formatted: str, draft: dict) -> str:
    """본문 끝에 실천 포인트·핵심 요약 보장 섹션 추가"""
    action_points = draft.get("action_points", [])
    one_line_summary = draft.get("one_line_summary", "")

    sections = "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    if action_points:
        sections += "\n✅ 오늘의 실천 포인트\n"
        for i, point in enumerate(action_points, 1):
            sections += f"  {i}. {point}\n"

    if one_line_summary:
        sections += f"\n📌 핵심 한 줄 요약\n  {one_line_summary}\n"

    sections += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return formatted + sections


def main():
    print("=" * 50)
    print("🤖 블로그 초안 봇 시작")
    print("=" * 50)

    # 1. 뉴스 수집
    print("\n📡 뉴스 수집 중...")
    articles = collect_all_news(hours_back=24)

    if not articles:
        print("❌ 수집된 뉴스 없음. 종료.")
        return

    # 2. 상위 기사 선별 (5건)
    top_articles = select_top_articles(articles, n=5)
    print(f"\n🔍 선별된 기사 {len(top_articles)}건:")
    for i, a in enumerate(top_articles, 1):
        print(f"  {i}. [{a['source']}] {a['title']}")

    # 3. Claude API 초안 생성
    print("\n")
    draft = generate_blog_draft(top_articles)

    # 3-1. 금지어 최종 검증
    BANNED_WORDS_FINAL = ["보험", "변액", "보험주", "보험사", "보장", "종신"]
    body_text = draft.get("body", "")
    for word in BANNED_WORDS_FINAL:
        if word in body_text:
            print(f"  ⚠️ [최종 검증] 금지어 '{word}'가 본문에 포함됨 — 수동 확인 필요")

    # 4. 네이버 블로그 포맷으로 변환
    formatted = format_for_naver_blog(draft)

    # 실천 포인트·핵심 요약을 본문 끝에 보장 섹션으로 추가
    formatted = _append_guaranteed_sections(formatted, draft)

    print("\n📨 텔레그램 전송 중...")
    kwargs = {
        "draft_text": formatted,
        "one_line_summary": draft.get("one_line_summary", ""),
    }
    if _SENDER_HAS_ACTION_POINTS:
        kwargs["action_points"] = draft.get("action_points", [])

    send_blog_draft(**kwargs)

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
