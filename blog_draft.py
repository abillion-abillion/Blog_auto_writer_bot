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

    # 4. 네이버 블로그 포맷으로 변환
    formatted = format_for_naver_blog(draft)

    # 5. 실천 포인트 / 핵심 요약을 본문 끝에 보장 섹션으로 직접 추가
    #    sender 버전과 무관하게 텔레그램에 반드시 포함됨
    action_points = draft.get("action_points", "")
    one_line_summary = draft.get("one_line_summary", "")

    guaranteed = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━"
    if action_points and action_points.strip():
        guaranteed += f"\n✅ [오늘의 실천 포인트]\n\n{action_points.strip()}"
    if one_line_summary and one_line_summary.strip():
        guaranteed += f"\n\n💡 [핵심 한 줄 요약]\n{one_line_summary.strip()}"
    guaranteed += "\n━━━━━━━━━━━━━━━━━━━━━━━━━"

    formatted_final = formatted + guaranteed

    # 6. 텔레그램 전송 - 구버전/신버전 sender 자동 감지
    print("\n📨 텔레그램 전송 중...")
    sig = inspect.signature(send_blog_draft)
    if "action_points" in sig.parameters:
        send_blog_draft(
            draft_text=formatted_final,
            one_line_summary=one_line_summary,
            action_points=action_points,
        )
    else:
        send_blog_draft(
            draft_text=formatted_final,
            one_line_summary=one_line_summary,
        )

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
