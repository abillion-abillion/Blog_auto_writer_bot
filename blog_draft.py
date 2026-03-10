"""
블로그 봇 메인 실행 파일
실행: python blog_draft.py
"""
import sys
import os

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

    # 5. 텔레그램 전송
    print("\n📨 텔레그램 전송 중...")
    send_blog_draft(
        draft_text=formatted,
        one_line_summary=draft.get("one_line_summary", "")
    )

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
