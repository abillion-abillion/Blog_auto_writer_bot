"""
Claude API를 이용한 네이버 블로그 초안 생성기
- 1단계: Haiku로 뉴스 선정 + 팩트 요약
- 2단계: Sonnet 4.6으로 고품질 블로그 초안 작성
"""
import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()

HAIKU_SELECTION_SYSTEM = """당신은 경제 뉴스 큐레이터입니다.
제공된 뉴스 기사 목록에서 블로그 포스팅에 가장 적합한 기사 1건을 선정하고,
기사 내용에서 확인 가능한 팩트만 정리합니다.

선정 기준:
- 30~50대 직장인/자영업자 자산에 직접 영향
- 구체적 수치·데이터 포함
- 배경 분석이 가능한 깊이
- 독자 행동을 이끌 수 있는 내용

출력 형식 (JSON만, 마크다운 코드블록 없이):
{
  "selected_index": 기사번호(1부터),
  "selected_title": "선정 기사 제목",
  "key_facts": ["기사에서 확인된 팩트1 (수치 포함)", "팩트2", "팩트3"],
  "selection_reason": "선정 이유 2~3줄",
  "seo_keyword": "핵심 SEO 키워드 1개"
}

절대 금지: 기사에 없는 수치·내용 추가"""

SYSTEM_PROMPT = """
## 당신은 누구인가

'허어머니(Heomoney)' 브랜드로 활동하는 자산관리사 남진우입니다.
JW파이낸셜 대표로 서울에서 5년간 100명 이상의 개인 자산을 관리해왔습니다.

---

## 팩트 원칙 (최우선 준수)

1. 제공된 뉴스 데이터에 명시된 내용만 사실로 작성
2. 기사에 없는 수치·통계는 절대 사용 금지
3. 전망·예측이 필요한 경우 반드시 [추정] 태그 명시
   예: "[추정] 금리가 추가 인하될 경우 부동산 수요가 회복될 수 있습니다."

---

## 브랜드 키워드 (반드시 삽입)

본문에 아래 키워드를 자연스럽게 각각 5회 이상 포함:
- JWfinancial
- JW파이낸셜

삽입 예시:
"JW파이낸셜에서 이 데이터를 분석한 결과..."
"JWfinancial 자산관리 관점에서 보면..."

---

## SEO 최적화

제공된 SEO 키워드를 본문에 자연스럽게 5회 이상 반복

---

## 글쓰기 핵심 원칙

1. 결론 먼저, 이유는 그 다음
2. 어려운 용어 즉시 풀이: "양적긴축(QT) → 연준이 채권을 팔아 시중 현금을 회수하는 정책"
3. 숫자는 실생활 규모로 환산 (기사에 있는 수치만)
4. 핵심 단어는 단독 줄에 강조
5. 고객 불안 공감 → 역사적 사례 → 합리적 안심
6. 짧은 단락, 줄바꿈 많이 (한 단락 2~4줄)

---

## 거시경제 논리 전개

- 하드 데이터 vs 소프트 데이터 구분
- 인과관계 화살표 체인: A → B → C
- 기본 시나리오 + 꼬리 리스크 구분
- 독자 상황별 행동 분기 (예금형/투자형/대출형)
- 글로벌 이슈는 반드시 한국 현실로 착지

---

## 독자 설정

- 30~50대 직장인/자영업자
- "내 돈에 어떤 영향인지만 알려줘"가 핵심 니즈

---

## 글의 구성 (반드시 이 순서)

1. 첫 문장: 질문으로 시작
2. 오늘의 핵심 한 줄
3. 왜 중요한가 (배경 3~5단락, 기사 팩트 중심)
4. 내 자산에 어떤 영향? (예금/주식/부동산 유형별)
5. JW파이낸셜 자산관리사 시각
6. 오늘의 실천 포인트 1~2개 (구체적 행동, 수치 포함)
7. CTA

---

## CTA (글 마지막에 반드시)

💬 오늘 내용이 내 상황에 어떻게 적용되는지 궁금하신가요?

5년간 100명 이상의 자산을 관리해온 JWfinancial 남진우 자산관리사가
여러분의 상황에 맞는 방향을 함께 찾아드립니다.

👉 30초 무료 재무진단: https://jwfinancial.co.kr/

---

## 절대 금지

- 특정 금융상품/종목 직접 추천
- "반드시 오른다", "확실하다" 단정적 표현
- "폭락", "대공황" 자극적 단어
- 기사에 없는 수치 임의 생성
- 500자 이상 긴 단락

---

## 출력 형식 (JSON만, 마크다운 코드블록 없이)

{
  "title": "블로그 제목 (클릭 유도, 30자 이내)",
  "subtitle": "부제목 (날짜 포함) | JW파이낸셜",
  "body": "본문 전체 (마크다운, 2000자 이상, CTA 포함)",
  "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
  "one_line_summary": "핵심 한 줄 요약 (팩트 기반)",
  "action_points": [
    "구체적 행동 1 (수치 포함)",
    "구체적 행동 2 (수치 포함)"
  ]
}
"""

USER_PROMPT_TEMPLATE = """아래 선정된 뉴스를 바탕으로 심층 분석 블로그 포스트를 작성해주세요.

=== 선정 기사 ===
{article_info}

=== 기사 기반 핵심 팩트 (이것만 수치로 사용) ===
{key_facts}

=== SEO 키워드 (5회 이상 자연 반복) ===
{seo_keyword}

=== 작성 가이드 ===
- 분량: 2000~3000자
- 팩트에 없는 수치는 반드시 [추정] 표시
- JWfinancial / JW파이낸셜 각 5회 이상 자연 삽입
- 작성일: {today}
"""


def format_news_for_selection(articles: List[Dict]) -> str:
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. [{art['source']}] {art['title']}")
        if art.get("summary"):
            lines.append(f"   요약: {art['summary'][:200]}")
        lines.append("")
    return "\n".join(lines)


def select_and_brief_with_haiku(articles: List[Dict]) -> Dict:
    """1단계: Haiku로 최적 기사 1건 선정 + 팩트 요약"""
    print("🔍 Haiku로 최적 기사 선정 중...")
    news_text = format_news_for_selection(articles)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=HAIKU_SELECTION_SYSTEM,
            messages=[{"role": "user", "content": f"뉴스 {len(articles)}건 중 최적 기사 선정:\n\n{news_text}"}],
        )
        raw = response.content[0].text.strip()
        brief = json.loads(raw.replace("```json", "").replace("```", "").strip())
        idx = brief.get("selected_index", 1) - 1
        selected = articles[idx] if 0 <= idx < len(articles) else articles[0]
        print(f"  ✓ 선정: [{selected['source']}] {selected['title']}")
        print(f"  ✓ SEO 키워드: {brief.get('seo_keyword', '')}")
        return {
            "article": selected,
            "key_facts": brief.get("key_facts", []),
            "seo_keyword": brief.get("seo_keyword", "재테크"),
        }
    except Exception as e:
        print(f"  ⚠️ Haiku 선정 실패 ({e}), 첫 번째 기사 폴백")
        return {
            "article": articles[0],
            "key_facts": [articles[0].get("summary", "")[:150]],
            "seo_keyword": "경제 재테크",
        }


def generate_blog_draft(articles: List[Dict]) -> Dict:
    """2단계: Sonnet 4.6으로 고품질 블로그 초안 생성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    brief = select_and_brief_with_haiku(articles)
    article = brief["article"]
    key_facts_text = "\n".join([f"- {f}" for f in brief["key_facts"]]) or "- 기사 요약 참고"
    article_info = (
        f"출처: {article['source']}\n"
        f"제목: {article['title']}\n"
        f"요약: {article.get('summary', '')}\n"
        f"링크: {article.get('link', '')}"
    )
    user_prompt = USER_PROMPT_TEMPLATE.format(
        article_info=article_info,
        key_facts=key_facts_text,
        seo_keyword=brief["seo_keyword"],
        today=today,
    )

    print("📝 Sonnet 4.6으로 블로그 초안 작성 중...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = response.content[0].text.strip()
    print(f"  ✓ 입력 토큰: {response.usage.input_tokens} / 출력 토큰: {response.usage.output_tokens}")

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        draft = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON 파싱 실패 ({e}), 폴백")
        draft = {
            "title": f"{today} 경제 브리핑 | JW파이낸셜",
            "subtitle": f"{today} 주요 경제 분석 | JW파이낸셜 남진우",
            "body": raw,
            "tags": ["경제", "재테크", "금융", "JWfinancial", "자산관리"],
            "one_line_summary": brief["seo_keyword"] + " 관련 주요 이슈",
            "action_points": ["현재 자산 배분 현황 점검", "전문가 상담 예약"],
        }

    if not draft.get("one_line_summary", "").strip():
        draft["one_line_summary"] = draft.get("title", today + " 경제 핵심")
    if not isinstance(draft.get("action_points"), list):
        draft["action_points"] = ["현재 자산 배분 현황 점검", "전문가 상담 예약"]

    return draft


def clean_body(text: str) -> str:
    text = text.replace("\\n", "\n").replace("\\t", "\t")
    lines = []
    for line in text.split("\n"):
        line = line.replace("*", "")
        if line.startswith("### "):
            lines.append(f"\n▶ {line[4:]}")
        elif line.startswith("## "):
            lines.append(f"\n━━ {line[3:]} ━━")
        elif line.startswith("# "):
            lines.append(f"\n◆ {line[2:]}")
        else:
            lines.append(line)
    return "\n".join(lines)


def format_for_naver_blog(draft: Dict) -> str:
    """텔레그램 전송용 본문 텍스트만 반환 (이미지·헤더 제외)"""
    return clean_body(draft.get("body", ""))
