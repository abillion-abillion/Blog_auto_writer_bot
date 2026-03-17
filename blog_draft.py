"""
블로그 봇 메인 실행 파일
실행: python blog_draft.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sources.rss_collector import collect_all_news, select_top_articles
from generator.claude_writer import generate_blog_draft, format_for_naver_blog
from sender.telegram_sender import send_blog_draft


def main():
    print("=" * 50)
    print("🤖 블로그 초안 봇 시작")
    print("=" * 50)

    print("\n📡 뉴스 수집 중...")
    articles = collect_all_news(hours_back=24)

    if not articles:
        print("❌ 수집된 뉴스 없음. 종료.")
        return

    top_articles = select_top_articles(articles, n=5)
    print(f"\n🔍 선별된 기사 {len(top_articles)}건:")
    for i, a in enumerate(top_articles, 1):
        print(f"  {i}. [{a['source']}] {a['title']}")

    print("\n")
    draft = generate_blog_draft(top_articles)

    formatted = format_for_naver_blog(draft)

    print("\n📨 텔레그램 전송 중...")
    send_blog_draft(
        draft_text=formatted,
        one_line_summary=draft.get("one_line_summary", "")
    )

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
