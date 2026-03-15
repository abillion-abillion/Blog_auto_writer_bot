"""
column.html 자동 업데이트 모듈
- blog_draft.py에서 생성된 초안을 column.html 카드 그리드 맨 앞에 삽입
- 실행: python html_publisher.py (단독 테스트용)
- blog_draft.py에서 import해서 사용
"""
import re
from datetime import datetime
from typing import Dict
from pathlib import Path

# 태그별 썸네일 스타일 (기존 column.html 패턴 그대로)
TAG_STYLES = {
    "절세":     {"gradient": "linear-gradient(135deg,#0e1a2b,#1a3a5c)", "emoji": "🏦"},
    "투자":     {"gradient": "linear-gradient(135deg,#1a0e0e,#2e1515)", "emoji": "📈"},
    "연금":     {"gradient": "linear-gradient(135deg,#1a1a0e,#2a2a0a)", "emoji": "🌿"},
    "부동산":   {"gradient": "linear-gradient(135deg,#0e1a14,#142a1e)", "emoji": "🏠"},
    "금융상품": {"gradient": "linear-gradient(135deg,#1a0e1a,#2a1530)", "emoji": "💳"},
    "경제":     {"gradient": "linear-gradient(135deg,#0e1520,#0d2040)", "emoji": "📊"},
    "금리":     {"gradient": "linear-gradient(135deg,#1a0e0e,#2e1515)", "emoji": "💹"},
    "환율":     {"gradient": "linear-gradient(135deg,#0e1a14,#142a1e)", "emoji": "💱"},
    "주식":     {"gradient": "linear-gradient(135deg,#1a0e0e,#2e1515)", "emoji": "📈"},
    "기타":     {"gradient": "linear-gradient(135deg,#141414,#1e1e1e)", "emoji": "📝"},
}

# column.html 삽입 기준점 (이 주석 바로 앞에 새 카드 삽입)
INSERT_MARKER = "<!-- 칼럼 1 -->"

# column.html 경로 (프로젝트 루트 기준)
COLUMN_HTML_PATH = Path(__file__).parent.parent / "column.html"


def pick_tag_style(tags: list) -> Dict[str, str]:
    """tags 목록에서 첫 번째로 매칭되는 스타일 반환"""
    for tag in tags:
        if tag in TAG_STYLES:
            return TAG_STYLES[tag]
    return TAG_STYLES["기타"]


def pick_primary_tag(tags: list) -> str:
    """필터 data-tags 속성에 쓸 주요 태그 1개 반환"""
    priority = ["절세", "투자", "연금", "부동산", "금융상품", "경제", "금리", "환율", "주식"]
    for p in priority:
        if p in tags:
            return p
    return tags[0] if tags else "기타"


def build_card_html(
    naver_url: str,
    title: str,
    excerpt: str,
    tags: list,
    date_str: str,          # "2026.03" 형식
    card_number: int = 1,   # 주석 번호 (1, 2, 3 ...)
) -> str:
    """col-card HTML 블록 생성"""
    style = pick_tag_style(tags)
    primary_tag = pick_primary_tag(tags)
    tag_label = primary_tag

    # 제목 150자, 요약 100자 이내로 자르기
    title   = title[:150]
    excerpt = excerpt[:100] + ("..." if len(excerpt) > 100 else "")

    return f"""
    <!-- 칼럼 {card_number} -->
    <a class="col-card" href="{naver_url}" target="_blank" data-tags="{primary_tag}">
      <div class="col-thumb" style="background: {style['gradient']};">
        <div class="col-thumb-emoji">{style['emoji']}</div>
        <div class="col-thumb-label">{tag_label}</div>
      </div>
      <div class="col-info">
        <div class="col-tag">{tag_label}</div>
        <div class="col-title">{title}</div>
        <div class="col-excerpt">{excerpt}</div>
        <div class="col-meta">
          <div class="col-meta-left">{date_str}</div>
          <div class="col-naver-badge">N 블로그</div>
        </div>
      </div>
    </a>
"""


def renumber_card_comments(html: str) -> str:
    """<!-- 칼럼 N --> 주석을 1부터 순서대로 재번호 매기기"""
    counter = [0]
    def replacer(m):
        counter[0] += 1
        return f"<!-- 칼럼 {counter[0]} -->"
    return re.sub(r"<!-- 칼럼 \d+ -->", replacer, html)


def insert_card_to_html(
    html_path: Path,
    naver_url: str,
    title: str,
    excerpt: str,
    tags: list,
) -> bool:
    """
    column.html을 읽어서 새 카드를 맨 앞(<!-- 칼럼 1 --> 위치)에 삽입.
    성공 시 True 반환.
    """
    if not html_path.exists():
        print(f"[html_publisher] ❌ 파일 없음: {html_path}")
        return False

    html = html_path.read_text(encoding="utf-8")

    if INSERT_MARKER not in html:
        print(f"[html_publisher] ❌ 삽입 기준점 없음: '{INSERT_MARKER}'")
        return False

    date_str = datetime.now().strftime("%Y.%m")
    new_card = build_card_html(
        naver_url=naver_url,
        title=title,
        excerpt=excerpt,
        tags=tags,
        date_str=date_str,
        card_number=1,
    )

    # 기준점 앞에 새 카드 삽입
    updated = html.replace(INSERT_MARKER, new_card + "    " + INSERT_MARKER, 1)

    # 카드 번호 재정렬 (1,2,3...)
    updated = renumber_card_comments(updated)

    html_path.write_text(updated, encoding="utf-8")
    print(f"[html_publisher] ✓ 카드 삽입 완료: {title[:40]}...")
    return True


def publish_to_html(draft: Dict, naver_url: str, html_path: Path = None) -> bool:
    """
    blog_draft.py에서 호출하는 메인 함수.

    사용 예:
        from publisher.html_publisher import publish_to_html
        publish_to_html(draft, naver_url="https://blog.naver.com/moneymustard/12345")
    """
    path = html_path or COLUMN_HTML_PATH
    title   = draft.get("title", "")
    excerpt = draft.get("one_line_summary", "")[:100]
    tags    = draft.get("tags", ["기타"])

    return insert_card_to_html(
        html_path=path,
        naver_url=naver_url,
        title=title,
        excerpt=excerpt,
        tags=tags,
    )


# ── 단독 테스트 ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    # 테스트용 더미 draft
    test_draft = {
        "title": "[테스트] 2026년 기준금리 인하, 내 예금과 대출에 미치는 영향",
        "one_line_summary": "한국은행이 기준금리를 3.0%로 동결. 하반기 인하 기대감 속 예금 전략을 재점검할 시점.",
        "tags": ["금리", "금융상품", "경제"],
    }
    test_url = "https://blog.naver.com/moneymustard/TEST_001"

    # column.html 경로를 인자로 받거나 기본값 사용
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else COLUMN_HTML_PATH

    ok = publish_to_html(test_draft, test_url, html_path=target_path)
    print("✅ 성공" if ok else "❌ 실패")
