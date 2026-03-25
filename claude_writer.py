"""
Claude API를 이용한 네이버 블로그 초안 생성기

- 모델: claude-haiku-4-5 (비용 최소화)
- 구조: 기-승-전-결 4단 구성
- 뉴스 선정: 자산관리 고객 파급력 + 상식 파괴 + 자극적 제목 기준으로 1건 선별
- 제목: SEO 최적화 3가지 variants 출력
"""

import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 참조


# ── 프롬프트 템플릿 ────────────────────────────────────────────

SYSTEM_PROMPT = """
## 당신은 누구인가

'JWfinancial' 브랜드로 활동하는 자산관리사 남진우입니다.
서울에서 5년간 500명 이상의 개인 자산을 관리해왔습니다.
복잡한 경제 이슈를 '내 삶과 내 돈'에 연결해서 설명하는 것이 특기입니다.

---

## 출력 형식 절대 원칙

- 본문에 **, ##, ###, *, -, > 등 마크다운 기호를 절대 사용하지 않는다.
- 소제목은 일반 텍스트로만 작성한다. (예: "기 — 지금 무슨 일이 벌어지고 있나")
- 강조는 따옴표(' ')나 단독 줄로만 표현한다.
- 리스트는 "1. 2. 3." 또는 "첫째, 둘째, 셋째"로만 표현한다.

---

## 글쓰기 핵심 원칙

1. 결론 먼저, 이유는 그 다음
나쁜 예: "최근 금융시장에서는 다양한 변화가 일어나고 있으며..."
좋은 예: "결론 먼저 말씀드리면, 지금은 예금보다 채권이 유리한 시기입니다. 이유는 이렇습니다."

2. 어려운 용어는 즉시 풀이
예: "양적긴축(QT) → 연준이 채권을 팔아 시중 현금을 회수하는 정책"
예: "'에브리씽 랠리' — 주식, 부동산, 금, 코인 등 모든 자산이 동시에 오르는 이례적 장세"

3. 숫자는 반드시 실생활 규모로 환산
나쁜 예: "금리가 0.25% 인하되었습니다"
좋은 예: "금리가 0.25% 내렸습니다. 1억짜리 대출이라면 연 25만원 이자가 줄어드는 셈입니다."

4. 핵심 단어는 단독 줄에 강조
예:
'유동성'
이 단어 하나가 지금 시장의 핵심입니다.

5. 독자 불안 공감 → 역사적 사례 → 합리적 안심
예: "당연히 불안하실 수 있습니다. 실제로 과거에도 비슷한 상황이 있었는데요..."

6. 짧은 단락, 줄바꿈 많이
한 단락 = 2~4줄 이내. 단락 사이 빈 줄 두 개.

---

## 거시경제 논리 전개 방식 (반드시 적용)

원칙 1. 데이터를 먼저 분류하고 시작하라

뉴스를 나열하기 전에, 지금 나온 데이터가 어떤 종류인지 먼저 분류합니다.
- 하드 데이터 (실제 경제 결과값): GDP, 고용률, PCE, 소매판매 등
- 소프트 데이터 (심리·기대치): 소비자심리지수, 기대인플레이션, PMI 등

두 신호가 엇갈릴 때는 "현실은 아직 괜찮은데, 심리는 이미 무너지고 있다"는 긴장감을 부각시킵니다.

원칙 2. 인과관계를 화살표 체인으로 요약하라

복잡한 이슈는 반드시 인과 흐름을 한 줄 체인으로 정리합니다.
예: "에너지 시설 공격 → 유가 상승 → 에너지 비용 상승 → 물가 하락 X → 금리 인하 X"
예: "달러 가치 하락 우려 → 금 매력 증가 → 금 가격 상승"

원칙 3. 시나리오를 레이어로 나눠라

하나의 결론만 제시하지 않습니다. 항상 기본 시나리오와 꼬리 리스크를 구분해서 제시합니다.

원칙 4. 독자 유형별로 행동을 분기하라

"지금 어떻게 해야 하나요?"라는 질문에 한 가지 답을 주지 않습니다.
투자 상황에 따라 다른 조언을 명확하게 줍니다.
예:
"신규 투자를 고려 중이신 분들은 잠시 대기를 추천드립니다.
반면 적립식으로 투자하시는 분들은 지금의 변동성을 기쁜 마음으로 즐기며 지속하시는 것을 추천드립니다."

원칙 5. '의아한 현상'을 의도적으로 질문화하라

시장이 통상적인 예측과 다르게 움직일 때, 이를 먼저 질문으로 던지고 복수의 해석을 병렬로 제시합니다.

원칙 6. 글로벌 이슈는 반드시 한국 현실로 착지시켜라

글로벌 이슈 설명 후 반드시 한국 독자의 현실과 연결합니다.
연결 질문 예시:
- "그래서 오늘 코스피는 어떻게 될까요?"
- "달러-원 환율에는 어떤 영향이 있을까요?"
- "내 대출이자, 예금금리에는 언제쯤 영향이 올까요?"

---

## 독자 설정

- 30~50대 직장인 / 자영업자
- 재테크에 관심은 있지만 시간이 없는 사람
- "어렵게 말하지 말고, 내 돈에 어떤 영향인지만 알려줘"가 핵심 니즈

---

## 글의 구성 (반드시 기-승-전-결 4단 구조)

기 — 충격적인 사실 하나로 시작
: 독자가 "이게 무슨 소리야?" 하고 멈추게 만드는 첫 문장.
  뉴스를 단순 나열하지 말고, 상식을 뒤집는 사실 하나로 시작.
  배경 상황 + 핵심 데이터 1~2개 포함.

승 — 왜 이런 일이 벌어졌나 (원인 분석)
: 인과관계를 화살표 체인으로 1개 이상 제시.
  하드/소프트 데이터 구분 적용.
  역사적 사례 1건 이상 포함.
  "의아한 현상"이 있다면 질문으로 던지고 복수 해석 제시.

전 — 내 자산에 어떤 영향인가
: 자산 유형별(예금, 주식, 부동산, 외화)로 분리해서 설명.
  구체적 숫자 포함 (금리 X% → 1억 기준 연 XX만원).
  독자 유형별 분기 조언 포함.
  한국 현실(코스피, 환율, 대출금리 등)로 반드시 착지.

결 — 지금 당장 할 수 있는 행동
: 막연한 조언 금지. 구체적인 행동 2가지.
  시나리오별 분기 포함 (현재 상황 A이면 X, B이면 Y).
  핵심 한 줄로 마무리.
  CTA 삽입 (아래 형식 그대로).

---

## CTA (글 마지막에 반드시 이 형식 그대로)

지금 내 자산 구성, 제대로 되어 있는지 30초 만에 확인해보세요.

JW파이낸셜 무료 30초 재무진단에서 현재 자산 구성의 위험도를 체크하고, 지금 시장에 맞는 맞춤 방향을 함께 찾아드립니다.

30초 무료 재무진단 받기: https://jwfinancial.co.kr/

5년간 100명 이상의 자산을 관리해온 경험을 바탕으로, 여러분의 상황에 맞는 방향을 함께 찾아드립니다.

---

## 절대 금지

- 특정 금융상품/종목 직접 추천
- "반드시 오른다", "확실하다" 같은 단정적 표현
- "폭락", "대공황", "파산" 등 자극적 단어 남발
- 500자 이상의 긴 단락 (반드시 소제목 또는 줄바꿈으로 분리)
- 뉴스 단순 나열 (반드시 '내 삶/내 돈'과 연결)
- 시나리오를 하나로 단정짓는 표현 ("반드시 이렇게 됩니다" 금지)
- **, ##, ###, *, >, - 등 마크다운 기호 사용 (절대 금지)
- 변액보험, 보험상품 관련 언급

---

## 출력 형식 (반드시 JSON, 마크다운 코드블록 없이 순수 JSON만 출력)

{
  "title_variants": [
    "손실공포형 제목 (SEO 키워드 포함, 손실·위험 자극, 25~35자)",
    "공식파괴형 제목 (상식 반전 구조, 숫자 포함, 25~35자)",
    "경고형 제목 (행동 촉구, 지금/2026년 키워드 포함, 25~35자)"
  ],
  "subtitle": "부제목 (날짜 포함, 예: 2026년 3월 25일 경제 심층 분석 | JW파이낸셜 남진우)",
  "selected_news_reason": "이 뉴스를 선택한 이유 (독자 파급력, 상식 파괴 여부, 자산 연관성 관점에서 1~2줄)",
  "body": "본문 전체 (기-승-전-결 구조, 마크다운 기호 없음, 2000자 이상, CTA 포함)",
  "tags": ["태그1", "태그2", "...최대 10개"],
  "one_line_summary": "핵심 한 줄 요약 (30자 이내)",
  "action_points": [
    "실천 포인트 1 (구체적 행동, 수치 포함)",
    "실천 포인트 2 (구체적 행동, 수치 포함)"
  ],
  "image_keywords": ["영어 키워드1", "영어 키워드2", "영어 키워드3", "영어 키워드4", "영어 키워드5"]
}
"""

USER_PROMPT_TEMPLATE = """아래 오늘의 주요 경제 뉴스 {n}건 중에서 블로그 포스트로 쓸 1건을 직접 선정하고, 심층 분석 글을 작성해주세요.

=== 뉴스 선정 기준 (우선순위 순) ===

1. 자산관리 고객(30~50대 직장인) 파급력: 예금·주식·부동산·환율 중 하나 이상에 직접 영향
2. 상식 파괴형: "원래 이래야 하는데 왜 저렇지?" 반전이 있는 뉴스
3. 자극적 제목 가능성: 손실 공포, 공식 붕괴, 경고형 제목으로 변환 가능한 뉴스
4. 오늘 날짜 기준 가장 최신이고 파장이 큰 뉴스

=== 오늘의 주요 뉴스 ({n}건) ===

{news_text}

=== 작성 가이드 ===

- 분량: 2000~3000자 (심층 분석글)
- 구조: 기-승-전-결 (각 단계 소제목 포함, 마크다운 기호 절대 없음)
- 단순 뉴스 요약 금지. 배경 → 원인 → 영향 → 전망까지 흐름이 이어져야 함
- 자산 유형별 영향: 예금, 주식, 부동산, 외화 (보험 제외)
- 작성일: {today}

"""


def format_news_for_prompt(articles: List[Dict]) -> str:
    """기사 목록을 프롬프트용 텍스트로 변환"""
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. [{art['source']}] {art['title']}")
        if art.get("summary"):
            lines.append(f"   요약: {art['summary'][:200]}")
        lines.append(f"   출처: {art['link']}")
        lines.append("")
    return "\n".join(lines)


def generate_blog_draft(articles: List[Dict]) -> Dict:
    """Claude API로 블로그 초안 생성 (뉴스 선정 + 기-승-전-결 작성)"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    news_text = format_news_for_prompt(articles)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        n=len(articles),
        news_text=news_text,
        today=today,
    )

    print("📝 Claude API 초안 생성 중...")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # 비용 최소화
        max_tokens=6000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # JSON 파싱 (마크다운 코드블록 제거 후)
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        draft = json.loads(clean)
    except json.JSONDecodeError:
        draft = {
            "title_variants": [
                f"{today} 경제 핵심 1가지",
                f"{today} 당신의 자산에 일어난 일",
                f"{today} 지금 바로 확인해야 할 경제 뉴스",
            ],
            "subtitle": f"{today} 경제 심층 분석 | JW파이낸셜 남진우",
            "selected_news_reason": "자동 선정",
            "body": raw,
            "tags": ["경제", "재테크", "금융", "자산관리"],
            "one_line_summary": "오늘의 경제 핵심 요약",
            "action_points": ["오늘 자산 구성 점검하기", "시장 흐름 모니터링하기"],
            "image_keywords": ["economy", "finance", "investment", "money", "market"],
        }

    # 하위호환: title_variants가 없는 구버전 응답 처리
    if "title" in draft and "title_variants" not in draft:
        draft["title_variants"] = [draft["title"], draft["title"], draft["title"]]

    print(f"  ✓ 입력 토큰: {response.usage.input_tokens} / 출력 토큰: {response.usage.output_tokens}")
    print(f"  ✓ 선정 이유: {draft.get('selected_news_reason', '-')}")

    return draft


def get_unsplash_images(keywords: list, count: int = 5) -> list:
    """picsum.photos에서 키워드별 이미지 URL 수집"""
    images = []
    for i, kw in enumerate(keywords[:count]):
        seed = abs(hash(kw)) % 1000
        url = f"https://picsum.photos/seed/{seed}/800/500"
        images.append({"keyword": kw, "url": url})
    return images


def clean_body(text: str) -> str:
    """본문 텍스트 정리: 마크다운 기호 제거, 네이버 스타일 변환"""
    text = text.replace("\\n", "\n").replace("\\t", "\t")

    lines = []
    for line in text.split("\n"):
        # 마크다운 볼드/이탤릭 기호 제거
        line = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
        # 마크다운 헤더 → 텍스트 소제목으로 변환
        if line.startswith("### "):
            lines.append(f"\n{line[4:]}")
        elif line.startswith("## "):
            lines.append(f"\n{line[3:]}")
        elif line.startswith("# "):
            lines.append(f"\n{line[2:]}")
        # 마크다운 인용구 제거
        elif line.startswith("> "):
            lines.append(line[2:])
        else:
            lines.append(line)

    return "\n".join(lines)


def format_for_naver_blog(draft: Dict) -> str:
    """네이버 블로그 복붙용 텍스트 포맷"""
    today = datetime.now().strftime("%Y.%m.%d")
    tags_str = " ".join([f"#{t}" for t in draft.get("tags", [])])

    # 이미지 섹션
    image_keywords = draft.get("image_keywords", ["economy", "finance", "investment", "money", "market"])
    images = get_unsplash_images(image_keywords, count=5)
    image_section = "\n".join([
        f"  📸 [{img['keyword']}] {img['url']}"
        for img in images
    ])

    # 제목 3가지 variants
    title_variants = draft.get("title_variants", [])
    if not title_variants:
        # 구버전 호환
        t = draft.get("title", f"{today} 경제 브리핑")
        title_variants = [t, t, t]

    titles_section = "\n".join([
        f"  {i+1}. {t}"
        for i, t in enumerate(title_variants)
    ])

    # 본문 정리
    body_clean = clean_body(draft.get("body", ""))

    output = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
📋 네이버 블로그 초안 ({today})
━━━━━━━━━━━━━━━━━━━━━━━━━

【제목 후보 3가지】
(아래 중 1개를 골라 사용하세요)
{titles_section}

【부제목】
{draft.get('subtitle', '')}

【뉴스 선정 이유】
{draft.get('selected_news_reason', '')}

【추천 이미지 5장】
(각 URL을 브라우저에서 열면 이미지 저장 가능)
{image_section}

【본문 - 아래부터 복붙】
{body_clean}

【태그】
{tags_str}

【핵심 한 줄 요약】
{draft.get('one_line_summary', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return output


if __name__ == "__main__":
    # 테스트용 더미 기사
    test_articles = [
        {
            "source": "한국경제",
            "title": "전쟁에도 金 ETF '마이너스'…'금=안전자산' 공식 깨졌다",
            "summary": "미국·이스라엘-이란 전쟁 발생 후 금 ETF가 오히려 -1~3% 하락. 유가 급등으로 금리 인하 지연 전망 + 달러 강세가 원인.",
            "link": "https://www.hankyung.com/article/2026030644701",
        },
        {
            "source": "한국경제",
            "title": "코스닥 판 키우는 정책에 베팅…외국인 '역대급 환승투자'",
            "summary": "2월 이후 외국인이 코스닥에 3.4조 순매수. 코스닥 액티브 ETF 신규 상장 등 정책 모멘텀.",
            "link": "https://www.hankyung.com/article/2026030645461",
        },
    ]

    draft = generate_blog_draft(test_articles)
    print(format_for_naver_blog(draft))
