"""
블로그 봇 메인 실행 파일
실행: python blog_draft.py
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from sources.rss_collector import collect_all_news, select_top_articles
from generator.claude_writer import generate_blog_draft, format_for_naver_blog
from sender.telegram_sender import send_blog_draft
from publisher.html_publisher import publish_to_html

# column.html 경로 (레포 루트에 있다고 가정)
COLUMN_HTML_PATH = Path(__file__).parent / "column.html"


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

    # 4. 네이버 블로그 포맷으로 변환 → Telegram 전송
    formatted = format_for_naver_blog(draft)
    print("\n📨 텔레그램 전송 중...")
    send_blog_draft(
        draft_text=formatted,
        one_line_summary=draft.get("one_line_summary", "")
    )

    # 5. 네이버 블로그 URL 입력 받기 (환경변수 또는 stdin)
    #
    #    ▶ 자동 모드 (GitHub Actions):
    #      NAVER_POST_URL 환경변수에 URL을 설정하면 자동으로 HTML 업데이트.
    #      예: NAVER_POST_URL=https://blog.naver.com/moneymustard/12345
    #
    #    ▶ 수동 모드 (로컬 실행):
    #      환경변수 없으면 터미널에서 URL 직접 입력.
    #      엔터만 누르면 HTML 업데이트 건너뜀.
    #
    naver_url = os.environ.get("NAVER_POST_URL", "").strip()

    if not naver_url:
        print("\n" + "=" * 50)
        print("📝 네이버 블로그에 글을 발행한 뒤, URL을 입력해주세요.")
        print("   (건너뛰려면 엔터)")
        print("   예: https://blog.naver.com/moneymustard/223XXXXXXX")
        print("=" * 50)
        try:
            naver_url = input("🔗 네이버 블로그 URL: ").strip()
        except EOFError:
            # CI 환경에서 stdin 없을 때
            naver_url = ""

    if naver_url:
        print("\n🌐 column.html 업데이트 중...")
        ok = publish_to_html(draft, naver_url=naver_url, html_path=COLUMN_HTML_PATH)
        if ok:
            print("  ✓ column.html 카드 삽입 완료")
        else:
            print("  ⚠ column.html 업데이트 실패 (로그 확인)")
    else:
        print("\n  ⏭  column.html 업데이트 건너뜀")

    print("\n✅ 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
