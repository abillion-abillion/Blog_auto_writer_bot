"""
Claude API를 이용한 네이버 블로그 초안 생성기
- 1단계: Haiku로 뉴스 선정 + 팩트 요약 (비용 최소화)
- 2단계: Sonnet 4.6으로 고품질 블로그 초안 작성
"""
import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 참조

# ── 1단계: Haiku 뉴스 선정 시스템 프롬프트 ───────────────────
HAIKU_SELECTION_SYSTEM = """당신은 경제 뉴스 큐레이터입니다.
제공된 뉴스 기사 목록에서 블로그 포스팅에 가장 적합한 기사 1건을 선정하고,
기사 내용에서 확인 가능한 팩트만 정리합니다.

선정 기준:
- 30~50대 직장인/자영업자 자산에 직접 영향
- 구체적 수치·데이터 포함
- 배경 분석이 가능한 깊이
- 독자 행동을 이끌 수 있는 내용

출력 형식 (반드시 JSON만, 마크다운 코드블록 없이):
{
  "selected_index": 기사번호(1부터),
  "selected_title": "선정 기사 제목",
  "key_facts": ["기사에서 확인된 팩트1 (수치 포함)", "팩트2", "팩트3"],
  "selection_reason": "선정 이유 2~3줄",
  "seo_keyword": "핵심 SEO 키워드 1개"
}

절대 금지: 기사에 없는 수치·내용 추가, 팩트 변경, 임의 생성"""

# ── 2단계: Sonnet 4.6 블로그 작성 시스템 프롬프트 ─────────────
SYSTEM_PROMPT = """
## 당신은 누구인가

'허어머니(Heomoney)' 브랜드로 활동하는 자산관리사 남진우입니다.
JW파이낸셜 대표로 서울에서 5년간 100명 이상의 개인 자산을 관리해왔습니다.
복잡한 경제 이슈를 '내 삶과 내 돈'에 연결해서 설명하는 것이 특기입니다.

---

## 팩트 원칙 (최우선 준수)

1. 제공된 뉴스 데이터에 명시된 내용만 사실로 작성합니다.
2. 기사에 없는 수치·통계는 절대 사용하지 않습니다.
3. 전망·예측·추측이 필요한 경우 반드시 문장 앞에 [추정] 태그를 붙입니다.
   예: "[추정] 금리가 추가 인하될 경우 부동산 수요가 회복될 수 있습니다."
4. 역사적 사례는 일반 상식 범위에서만 언급하고, 구체적 수치는 [추정] 처리합니다.

---

## 브랜드 키워드 (반드시 삽입)

본문에 아래 키워드를 자연스럽게 각각 5회 이상 포함합니다.
- JWfinancial
- JW파이낸셜

삽입 예시:
"JW파이낸셜에서 이 데이터를 분석한 결과..."
"JWfinancial 자산관리 관점에서 보면..."
"JW파이낸셜 남진우 자산관리사는 이렇게 판단합니다."

---

## SEO 최적화

제공된 SEO 키워드를 본문에 자연스럽게 5회 이상 반복합니다.

---

## 글쓰기 핵심 원칙

1. 결론 먼저, 이유는 그 다음
   나쁜 예: "최근 금융시장에서는 다양한 변화가..."
   좋은 예: "결론 먼저 말씀드리면, 지금은 예금보다 채권이 유리한 시기입니다."

2. 어려운 용어는 즉시 풀이 (화살표 또는 괄호)
   예: "양적긴축(QT) → 연준이 채권을 팔아 시중 현금을 회수하는 정책"

3. 숫자는 실생활 규모로 환산 (기사에 있는 수치만 사용)
   예: "금리 0.25% 인하 → 1억 대출 기준 연 25만원 이자 절감"

4. 핵심 단어는 단독 줄에 강조

5. 고객 불안 공감 → 역사적 사례 → 합리적 안심

6. 짧은 단락, 줄바꿈 많이 (한 단락 2~4줄)

---

## 거시경제 논리 전개

- 하드 데이터(GDP·고용·소매판매) vs 소프트 데이터(심리지수·PMI) 구분
- 인과관계를 화살표 체인으로 요약: A → B → C
- 기본 시나리오 + 꼬리 리스크 구분
- 독자 상황별 행동 분기 (예금형/투자형/대출형)
- 글로벌 이슈는 반드시 한국 현실로 착지

---

## 독자 설정

- 30~50대 직장인/자영업자
- 재테크에 관심은 있지만 시간이 없는 사람
- "어렵게 말하지 말고, 내 돈에 어떤 영향인지만 알려줘"가 핵심 니즈

---

## 글의 구성 (반드시 이 순서)

1. 첫 문장: 질문으로 시작 (호기심 유발)
2. 오늘의 핵심 한 줄
3. 왜 중요한가 (배경 3~5단락, 기사 팩트 중심)
4. 내 자산에 어떤 영향? (예금/주식/부동산 유형별, 기사 수치 활용)
5. JW파이낸셜 자산관리사 시각과 판단 근거
6. 오늘의 실천 포인트 1~2개 (구체적 행동, 수치 포함)
7. CTA

---

## CTA (글 마지막에 반드시 이 형식 그대로)

💬 오늘 내용이 내 상황에 어떻게 적용되는지 궁금하신가요?

5년간 100명 이상의 자산을 관리해온 JWfinancial 남진우 자산관리사가
여러분의 상황에 맞는 방향을 함께 찾아드립니다.

👉 30초 무료 재무진단: https://jwfinancial.co.kr/

---

## 절대 금지

- 특정 금융상품/종목 직접 추천
- "반드시 오른다", "확실하다" 등 단정적 표현
- "폭락", "대공황", "파산" 등 자극적 단어 남발
- 기사에 없는 수치 임의 생성
- 500자 이상의 긴 단락

---

## 출력 형식 (반드시 JSON만, 마크다운 코드블록 없이)

{
  "title": "블로그 제목 (클릭 유도, 30자 이내)",
  "subtitle": "부제목 (날짜 포함, 예: 2026년 5월 18일 경제 브리핑 | JW파이낸셜)",
  "body": "본문 전체 (마크다운 형식, 위 구성 순서 준수, CTA 포함, 2000자 이상)",
  "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
  "one_line_summary": "핵심 한 줄 요약 (팩트 기반, 20자 이내)",
  "action_points": [
    "구체적 행동 1 (수치 포함, 예: 현재 주담대 변동금리 X% 확인 후 고정 전환 시뮬레이션)",
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
- 분량: 2000~3000자 (심층 분석글)
- 위 팩트에 있는 내용만 수치로 사용. 없는 수치는 반드시 [추정] 표시
- 배경 → 원인 → 영향 → 전망 흐름
- JWfinancial / JW파이낸셜 각 5회 이상 자연 삽입
- 작성일: {today}
"""


def format_news_for_selection(articles: List[Dict]) -> str:
    """기사 목록을 Haiku 선정용 텍스트로 변환"""
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. [{art['source']}] {art['title']}")
        if art.get("summary"):
            lines.append(f"   요약: {art['summary'][:200]}")
        lines.append("")
    return "\n".join(lines)


def select_and_brief_with_haiku(articles: List[Dict]) -> Dict:
    """
    1단계: Haiku로 최적 기사 1건 선정 + 팩트 요약
    실패 시 첫 번째 기사로 폴백
    """
    print("🔍 Haiku로 최적 기사 선정 중...")
    news_text = format_news_for_selection(articles)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=HAIKU_SELECTION_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"아래 뉴스 {len(articles)}건 중 최적 기사를 선정해주세요.\n\n{news_text}"
            }],
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
            "selection_reason": brief.get("selection_reason", ""),
            "seo_keyword": brief.get("seo_keyword", "재테크"),
        }

    except Exception as e:
        print(f"  ⚠️ Haiku 선정 실패 ({e}), 첫 번째 기사로 폴백")
        return {
            "article": articles[0],
            "key_facts": [articles[0].get("summary", "")[:100]],
            "selection_reason": "자동 폴백",
            "seo_keyword": "경제 재테크",
        }


def generate_blog_draft(articles: List[Dict]) -> Dict:
    """
    2단계: Sonnet 4.6으로 고품질 블로그 초안 생성
    """
    today = datetime.now().strftime("%Y년 %m월 %d일")

    # 1단계: Haiku 선정
    brief = select_and_brief_with_haiku(articles)
    article = brief["article"]
    key_facts_text = "\n".join([f"- {f}" for f in brief["key_facts"]])
    article_info = (
        f"출처: {article['source']}\n"
        f"제목: {article['title']}\n"
        f"요약: {article.get('summary', '')}\n"
        f"링크: {article.get('link', '')}"
    )

    user_prompt = USER_PROMPT_TEMPLATE.format(
        article_info=article_info,
        key_facts=key_facts_text if key_facts_text else "- 기사 요약 참고",
        seo_keyword=brief["seo_keyword"],
        today=today,
    )

    # 2단계: Sonnet 4.6 작성
    print("📝 Sonnet 4.6으로 블로그 초안 작성 중...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    print(f"  ✓ 입력 토큰: {response.usage.input_tokens} / 출력 토큰: {response.usage.output_tokens}")

    # JSON 파싱
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        draft = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON 파싱 실패 ({e}), 폴백 처리")
        draft = {
            "title": f"{today} 경제 브리핑 | JW파이낸셜",
            "subtitle": f"{today} 주요 경제 분석 | JW파이낸셜 남진우",
            "body": raw,
            "tags": ["경제", "재테크", "금융", "JWfinancial", "자산관리"],
            "one_line_summary": brief["seo_keyword"] + " 관련 주요 이슈",
            "action_points": ["현재 자산 배분 현황 점검", "전문가 상담 예약"],
        }

    # one_line_summary 빈값 방지
    if not draft.get("one_line_summary", "").strip():
        draft["one_line_summary"] = draft.get("title", today + " 경제 핵심")

    # action_points 타입 보장 (리스트)
    if not isinstance(draft.get("action_points"), list):
        draft["action_points"] = ["현재 자산 배분 현황 점검", "전문가 상담 예약"]

    return draft


def clean_body(text: str) -> str:
    """본문 텍스트 정리: 줄바꿈 처리 + 마크다운 기호 제거"""
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


if __name__ == "__main__":
    test_articles = [
        {
            "source": "한국경제",
            "title": "주택담보대출 5.5조 급증, 규제 강화에도 역대 최대",
            "summary": "금융당국의 규제 강화에도 불구하고 4월 주택담보대출이 5조5천억원 증가했다. 8개월 만에 최대 증가폭이다.",
            "link": "https://hankyung.com/test",
        }
    ]
    draft = generate_blog_draft(test_articles)
    print("\n=== 생성 결과 ===")
    print(f"제목: {draft.get('title')}")
    print(f"핵심: {draft.get('one_line_summary')}")
    print(f"실천: {draft.get('action_points')}")
