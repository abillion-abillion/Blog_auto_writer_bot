"""
경제 뉴스 RSS + 금감원/한은 공시 수집기
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# ── RSS 소스 목록 ──────────────────────────────────────────────
RSS_SOURCES = {
    "연합뉴스_경제": "https://www.yonhapnewstv.co.kr/category/news/economy/feed/",
    "한국경제":      "https://www.hankyung.com/feed/economy",
    "매일경제":      "https://www.mk.co.kr/rss/30100041/",
    "서울경제":      "https://www.sedaily.com/RSS/",
    "한국은행":      "https://www.bok.or.kr/portal/bbs/B0000220/list.do?menuNo=200069&pageIndex=1&searchCnd=&searchWrd=&rssYn=Y",
    "금융감독원":    "https://www.fss.or.kr/fss/kr/bbs/list.jsp?bbsid=1217592&menuNo=310006&rss=Y",
}

def fetch_rss(url: str, source_name: str, hours_back: int = 24) -> List[Dict]:
    """RSS 피드에서 최근 기사 수집"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=hours_back)

    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:  # 최대 10개
            # 날짜 파싱
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # 24시간 이내 기사만
            if pub_date and pub_date < cutoff:
                continue

            articles.append({
                "source": source_name,
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", "")[:300].strip(),
                "link": entry.get("link", ""),
                "published": pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "날짜 불명",
            })
    except Exception as e:
        print(f"[RSS 수집 오류] {source_name}: {e}")

    return articles


def collect_all_news(hours_back: int = 24) -> List[Dict]:
    """모든 소스에서 뉴스 수집 후 반환"""
    all_articles = []
    for name, url in RSS_SOURCES.items():
        articles = fetch_rss(url, name, hours_back)
        all_articles.extend(articles)
        print(f"  ✓ {name}: {len(articles)}건")

    # 최신순 정렬
    all_articles.sort(key=lambda x: x["published"], reverse=True)
    print(f"\n총 {len(all_articles)}건 수집 완료")
    return all_articles


def select_top_articles(articles: List[Dict], n: int = 5) -> List[Dict]:
    """
    블로그 초안용 상위 기사 선택
    - 중복 제목 제거
    - 금융/경제 키워드 우선
    """
    PRIORITY_KEYWORDS = [
        "금리", "환율", "주가", "코스피", "달러", "인플레이션", "기준금리",
        "한국은행", "금감원", "부동산", "ETF", "채권", "연준", "Fed",
        "물가", "경기", "GDP", "수출", "무역"
    ]

    scored = []
    seen_titles = set()

    for art in articles:
        title = art["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)

        score = sum(1 for kw in PRIORITY_KEYWORDS if kw in title or kw in art["summary"])
        scored.append((score, art))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [art for _, art in scored[:n]]


if __name__ == "__main__":
    articles = collect_all_news()
    top = select_top_articles(articles)
    print("\n=== 선별된 상위 기사 ===")
    for i, a in enumerate(top, 1):
        print(f"{i}. [{a['source']}] {a['title']}")

