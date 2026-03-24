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


CATEGORY_KEYWORDS = {
    "경제_금융": [
        "금리", "환율", "주가", "코스피", "달러", "인플레이션", "기준금리",
        "한국은행", "금감원", "ETF", "채권", "연준", "Fed", "물가", "GDP",
    ],
    "부동산": [
        "부동산", "아파트", "전세", "매매", "분양", "재건축", "임대", "주택",
    ],
    "정치_정책": [
        "정부", "대통령", "국회", "정책", "법안", "예산", "세금", "규제",
        "탄핵", "선거", "여당", "야당", "장관", "부처",
    ],
    "국제_통상": [
        "미국", "중국", "트럼프", "관세", "무역", "수출", "수입", "지정학",
        "러시아", "중동", "EU", "일본", "반도체", "공급망",
    ],
}

CATEGORY_QUOTA = {
    "경제_금융": 2,
    "부동산": 1,
    "정치_정책": 1,
    "국제_통상": 1,
}


def categorize_article(art: Dict) -> str:
    """기사를 카테고리로 분류 (가장 높은 점수 카테고리)"""
    text = art["title"] + " " + art["summary"]
    scores = {cat: sum(1 for kw in kws if kw in text)
              for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "기타"


def select_top_articles(articles: List[Dict], n: int = 5) -> List[Dict]:
    """
    카테고리별 쿼터를 맞춰 균형있게 상위 기사 선택
    - 중복 제목 제거
    - 카테고리별 할당: 경제2 + 부동산1 + 정치정책1 + 국제통상1
    """
    seen_titles = set()
    buckets: Dict[str, List] = {cat: [] for cat in CATEGORY_QUOTA}
    buckets["기타"] = []

    for art in articles:
        title = art["title"]
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        cat = categorize_article(art)
        text = art["title"] + " " + art["summary"]
        score = sum(1 for kws in CATEGORY_KEYWORDS.values() for kw in kws if kw in text)
        buckets.setdefault(cat, []).append((score, art))

    # 각 버킷 점수 정렬
    for cat in buckets:
        buckets[cat].sort(key=lambda x: x[0], reverse=True)

    selected = []
    # 쿼터대로 먼저 채우기
    for cat, quota in CATEGORY_QUOTA.items():
        picked = [art for _, art in buckets[cat][:quota]]
        selected.extend(picked)

    # n개 미달이면 남은 기사로 채우기
    if len(selected) < n:
        used_titles = {a["title"] for a in selected}
        leftovers = [
            art for _, art in
            sorted(
                [(s, a) for cat_list in buckets.values() for s, a in cat_list
                 if a["title"] not in used_titles],
                key=lambda x: x[0], reverse=True
            )
        ]
        selected.extend(leftovers[:n - len(selected)])

    return selected[:n]


if __name__ == "__main__":
    articles = collect_all_news()
    top = select_top_articles(articles)
    print("\n=== 선별된 상위 기사 ===")
    for i, a in enumerate(top, 1):
        print(f"{i}. [{a['source']}] {a['title']}")

