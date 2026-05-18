"""
블로그 봇 메인 실행 파일
실행: python blog_draft.py

파이프라인:
1. RSS 뉴스 수집
2. Haiku로 최적 기사 선정 + 팩트 요약
3. Sonnet 4.6으로 고품질 블로그 초안 작성
4. 텔레그램 3개 메시지로 전송
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

    # 1. 뉴스 수집
    print("\n📡 뉴스 수집 중...")
    articles = collect_all_news(hours_back=24)

    if not articles:
        print("❌ 수집된 뉴스 없음. 종료.")
        return

    # 2. 상위 기사 선별 (Haiku 선정을 위한 후보풀, 최대 10건)
    top_articles = select_top_articles(articles, n=10)
    print(f"\n🔍 후보 기사 {len(top_articles)}건:")
    for i, a in enumerate(top_articles, 1):
        print(f"  {i}. [{a['source']}] {a['title']}")

    # 3. Haiku 선정 + Sonnet 4.6 초안 생성
    print("\n")
    draft = generate_blog_draft(top_articles)

    # 4. 본문 텍스트 정리 (마크다운 → 텍스트)
    body_text = format_for_naver_blog(draft)

    # 5. 텔레그램 3개 메시지 전송
    print("\n📨 텔레그램 전송 중...")
    send_blog_draft(
        title=draft.get("title", ""),
        subtitle=draft.get("subtitle", ""),
        body=body_text,
        tags=draft.get("tags", []),
        one_line_summary=draft.get("one_line_summary", ""),
        action_points=draft.get("action_points", []),
    )

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
