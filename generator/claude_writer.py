"""
Claude API를 이용한 네이버 블로그 초안 생성기

- 모델: claude-haiku-4-5 (비용 최소화)
- 구조: 기-승-전-결 4단 구성
- 뉴스 선정: 자산관리 고객 파급력 + 상식 파괴 + 자극적 제목 기준으로 1건 선별
- 제목: SEO 최적화 3가지 variants 출력
- 금지: 마크다운 기호, 보험 관련 언급, 가짜 출처
"""

import anthropic
import json
import re
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 참조


# ── 금지어 목록 ───────────────────────────────────────────────
BANNED_WORDS = ["보험", "변액보험", "변액", "보험주", "보험사", "보장", "보장성", "종신"]


# ── 프롬프트 템플릿 ────────────────────────────────────────────

SYSTEM_PROMPT = """
=== 절대 규칙 (ABSOLUTE RULES — 어떤 상황에서도 예외 없음) ===

1. 마크다운 기호 절대 금지
   **, ##, ###, *, -, >, ``` 등 모든 마크다운 기호 사용 금지.
   강조가 필요하면 문맥으로 표현하거나 따옴표(' ')를 사용할 것.
   잘못된 예: **지금이 타이밍입니다**
   올바른 예: 지금이 타이밍입니다.

2. 금지 키워드 (절대 언급 불가)
   보험, 변액보험, 변액, 보험주, 보험사, 보장, 보장성, 종신
   이 단어들은 본문, 태그, 요약 어디에도 포함하면 안 됩니다.

3. 자산 카테고리 제한
   허용: 예적금, 주식, 부동산, 외화
   그 외 금융상품군(보험, 파생상품 등) 언급 금지.

4. 브랜드 표기 통일
   항상: JW파이낸셜
   금지: JWfinancial, JW Financial, JW 파이낸셜(띄어쓰기), jwfinancial

5. 출처 규칙
   뉴스 기사에서 가져온 실제 정보만 인용할 것.
   출처명, 연구기관명, 데이터 출처를 절대 창작하지 말 것.
   "핀사이트랩스" 등 실존하지 않는 기관명 사용 절대 금지.
   확인 불가한 통계는 "시장 분석에 따르면" 등 일반적 표현 사용.

6. 본문 길이: 2,000~3,000자 (공백 포함). 이 범위를 벗어나지 말 것.

=== 당신은 누구인가 ===

'허머니(Heomoney)' 브랜드로 활동하는 자산관리사 남진우입니다.
JW파이낸셜 대표로 서울에서 5년간 100명 이상의 개인 자산을 관리해왔습니다.
복잡한 경제 이슈를 '내 삶과 내 돈'에 연결해서 설명하는 것이 특기입니다.

=== 글쓰기 핵심 원칙 ===

1. 결론 먼저, 이유는 그 다음
   나쁜 예: "최근 금융시장에서는 다양한 변화가 일어나고 있으며..."
   좋은 예: "결론 먼저 말씀드리면, 지금은 예금을 고금리로 묶어둘 마지막 기회입니다."

2. 어려운 용어는 즉시 풀이
   예: "양적긴축(QT) → 연준이 채권을 팔아 시중 현금을 회수하는 정책"

3. 숫자는 반드시 실생활 규모로 환산
   나쁜 예: "금리가 0.25% 인하되었습니다"
   좋은 예: "금리가 0.25% 내렸습니다. 1억짜리 대출이라면 연 25만원 이자가 줄어드는 셈입니다."

4. 핵심 단어는 단독 줄에 강조 (따옴표 사용)
   예:
   '유동성'
   이 단어 하나가 지금 시장의 핵심입니다.

5. 인과관계를 화살표 체인으로 요약
   예: "에너지 시설 공격 → 유가 상승 → 물가 상승 → 금리 인하 불가"

6. 시나리오를 레이어로 구분
   하나의 결론만 제시하지 말 것. 기본 시나리오와 꼬리 리스크를 구분해서 제시.

7. 글로벌 이슈는 반드시 한국 현실로 착지
   "그래서 내 대출이자는?", "환율에는?", "국내 물가에는?"

8. 짧은 단락, 줄바꿈 많이
   한 단락 = 2~4줄 이내. 단락 사이 빈 줄 두 개.

9. 서술체 위주, 번호 리스트는 본문 전체에서 3개 이내로 최소화

=== 글의 구조 (반드시 기-승-전-결 4파트) ===

기 (도입): 독자가 "이게 무슨 소리야?" 하고 멈추게 만드는 첫 문장.
  상식을 뒤집는 사실 하나로 시작. 핵심 결론을 먼저 제시.
  배경 상황 + 핵심 데이터 1~2개 포함.

승 (전개): 왜 이런 일이 벌어졌는지 배경, 원인, 인과관계 분석.
  화살표 체인 1개 이상 제시.
  역사적 사례 1건 이상 포함.
  "의아한 현상"이 있다면 질문으로 던지고 복수 해석 제시.

전 (전환): 자산 유형별(예적금, 주식, 부동산, 외화) 구체적 대응 방법.
  구체적 숫자 포함 (금리 X% → 1억 기준 연 XX만원).
  독자 유형별 분기 조언 포함.
  한국 현실(코스피, 환율, 대출금리 등)로 반드시 착지.

결 (결론): 오늘 당장 실행할 수 있는 구체적 행동 2~3가지.
  시나리오별 분기 포함.
  핵심 한 줄로 마무리.
  CTA 삽입 (아래 형식 그대로).

소제목 형식 (plain text만):
  올바른 예: 기. 당신의 대출 이자가 달라졌습니다
  잘못된 예: ## 배경 분석
  잘못된 예: ━━ 왜 지금 금리가 이렇게 뛰었나? ━━

=== 독자 설정 ===

30~50대 직장인 / 자영업자
재테크에 관심은 있지만 시간이 없는 사람
"어렵게 말하지 말고, 내 돈에 어떤 영향인지만 알려줘"가 핵심 니즈

=== 톤 앤 보이스 ===

따뜻하지만 직설적, 전문적이지만 쉬운 말.
"~입니다" 체 사용.
JW파이낸셜 실제 경험(100명 이상 관리)을 자연스럽게 녹일 것.

=== 절대 금지 ===

특정 금융상품/종목 직접 추천
"반드시 오른다", "확실하다" 같은 단정적 표현
"폭락", "대공황", "파산" 등 자극적 단어 남발
500자 이상의 긴 단락 (반드시 소제목 또는 줄바꿈으로 분리)
뉴스 단순 나열 (반드시 '내 삶/내 돈'과 연결)
시나리오를 하나로 단정짓는 표현 ("반드시 이렇게 됩니다" 금지)
보험, 변액보험 등 금지 키워드 언급

=== 출력 형식 (반드시 JSON, 마크다운 코드블록 없이 순수 JSON만 출력) ===

{
  "title_variants": [
    "손실공포형 제목 (SEO 키워드 포함, 손실/위험 자극, 25~35자)",
    "상식파괴형 제목 (상식 반전 구조, 숫자 포함, 25~35자)",
    "경고행동형 제목 (행동 촉구, 지금/2026년 키워드 포함, 25~35자)"
  ],
  "subtitle": "부제목 (날짜 포함, 예: 2026년 3월 25일 경제 심층 분석 | JW파이낸셜 남진우)",
  "selected_news_reason": "이 뉴스를 선택한 이유 (독자 파급력, 상식 파괴 여부, 자산 연관성 관점에서 1~2줄)",
  "body": "본문 전체 (기-승-전-결 구조, 마크다운 기호 없음, 2000~3000자, CTA 포함)",
  "tags": ["태그1", "태그2", "...최대 10개"],
  "one_line_summary": "핵심 한 줄 요약 (30자 이내)",
  "action_points": [
    "실천 포인트 1 (구체적 행동, 수치 포함)",
    "실천 포인트 2 (구체적 행동, 수치 포함)"
  ],
  "image_keywords": ["영어 키워드1", "영어 키워드2", "영어 키워드3", "영어 키워드4", "영어 키워드5"]
}

제목 3종 작성 규칙:
손실공포형: 놓치면 얼마를 잃는지 구체적 금액/수치 포함
상식파괴형: 통념을 뒤집는 반전, "~인 줄 알았다면" 패턴
경고행동형: 지금 행동하지 않으면 안 되는 이유, 긴급성 강조
"""

USER_PROMPT_TEMPLATE = """아래 오늘의 주요 경제 뉴스 {n}건 중에서 블로그 포스트로 쓸 1건을 직접 선정하고, 심층 분석 글을 작성해주세요.

=== 뉴스 선정 기준 (우선순위 순) ===

1. 자산관리 고객(30~50대 직장인) 파급력: 예적금/주식/부동산/환율 중 하나 이상에 직접 영향
2. 상식 파괴형: "원래 이래야 하는데 왜 저렇지?" 반전이 있는 뉴스
3. 자극적 제목 가능성: 손실 공포, 공식 붕괴, 경고형 제목으로 변환 가능한 뉴스
4. 오늘 날짜 기준 가장 최신이고 파장이 큰 뉴스

=== 오늘의 주요 뉴스 ({n}건) ===

{news_text}

=== 작성 가이드 ===

- 분량: 2,000~3,000자 (이 범위를 반드시 지킬 것)
- 단순 뉴스 요약 금지. 배경 → 원인 → 영향 → 전망까지 흐름이 이어져야 함
- 구조: 반드시 기-승-전-결 4파트 (각 단계 소제목 포함, 마크다운 기호 절대 없음)
  기: 핵심 이슈 1개 선택 + 충격적 사실로 시작
  승: 왜 이 이슈가 중요한지 배경과 인과관계
  전: 자산 유형별(예적금/주식/부동산/외화) 영향과 대응
  결: 오늘 당장 실행할 수 있는 행동 2~3개 + CTA
- 보험, 변액보험, 보험주 등은 절대 언급하지 말 것
- 마크다운 기호(**, ##, -, * 등) 절대 사용 금지
- 출처명을 창작하지 말 것 (핀사이트랩스 등 가짜 기관명 금지)
- 작성일: {today}

=== CTA (본문 마지막에 아래 문구를 그대로 삽입) ===

지금 내 자산과 부채 상황에 맞는 최적의 방향이 궁금하시다면,
5년간 100명 이상의 자산을 관리해온 경험을 바탕으로 함께 찾아드리겠습니다.

30초 무료 재무진단 받기: https://jwfinancial.co.kr/
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


def _post_process(draft: Dict) -> Dict:
    """금지어 제거 + 마크다운 기호 제거 + CTA 검증 후처리"""
    body = draft.get("body", "")

    # 1. 마크다운 기호 제거
    body = body.replace("**", "")
    body = body.replace("##", "")
    body = body.replace("###", "")
    body = re.sub(r"^#+\s", "", body, flags=re.MULTILINE)

    # 2. 금지어 경고 로그
    for word in BANNED_WORDS:
        if word in body:
            print(f"  ⚠️ 금지어 발견: '{word}' — 해당 문장을 검토하세요")

    draft["body"] = body

    # 3. CTA 검증
    if "jwfinancial.co.kr" not in body:
        print("  ⚠️ CTA 링크(jwfinancial.co.kr)가 본문에 없습니다")
    if "30초 무료 재무진단" not in body and "무료 재무진단" not in body:
        print("  ⚠️ CTA 문구(30초 무료 재무진단)가 본문에 없습니다")

    # 4. 브랜드 표기 통일 (URL 내의 jwfinancial은 유지)
    body = body.replace("JWfinancial", "JW파이낸셜")
    body = body.replace("JW Financial", "JW파이낸셜")
    # URL 복원
    body = body.replace("JW파이낸셜.co.kr", "jwfinancial.co.kr")
    draft["body"] = body

    return draft


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
            "selected_news_reason": "자동 선정 (JSON 파싱 실패)",
            "body": raw,
            "tags": ["경제", "재테크", "금융", "자산관리"],
            "one_line_summary": "오늘의 경제 핵심 요약",
            "action_points": ["오늘 자산 구성 점검하기", "시장 흐름 모니터링하기"],
            "image_keywords": ["economy", "finance", "investment", "money", "market"],
        }

    # 하위호환: title_variants가 없는 구버전 응답 처리
    if "title" in draft and "title_variants" not in draft:
        draft["title_variants"] = [draft["title"], draft["title"], draft["title"]]

    # title 필드 호환성 유지
    if "title_variants" in draft and isinstance(draft["title_variants"], list) and draft["title_variants"]:
        draft["title"] = draft["title_variants"][0]

    # 후처리: 금지어 필터 + 마크다운 제거 + CTA 검증
    draft = _post_process(draft)

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
    """본문 텍스트 정리: 마크다운 기호 완전 제거, plain text 변환"""
    text = text.replace("\\n", "\n").replace("\\t", "\t")

    lines = []
    for line in text.split("\n"):
        # 마크다운 볼드/이탤릭 기호 완전 제거
        line = line.replace("**", "").replace("__", "").replace("*", "")
        # 마크다운 헤더 → plain text 소제목
        if line.startswith("### "):
            lines.append(f"\n{line[4:]}")
        elif line.startswith("## "):
            lines.append(f"\n{line[3:]}")
        elif line.startswith("# "):
            lines.append(f"\n{line[2:]}")
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
        t = draft.get("title", f"{today} 경제 브리핑")
        title_variants = [t, t, t]

    labels = ["손실공포형", "상식파괴형", "경고행동형"]
    titles_section = "\n".join([
        f"  [{labels[i] if i < len(labels) else f'변형{i+1}'}] {t}"
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
            "summary": "미국·이스라엘-이란 전쟁 발생 후 금 ETF가 오히려 -1~3% 하락.",
            "link": "https://www.hankyung.com/article/2026030644701",
        },
    ]

    draft = generate_blog_draft(test_articles)
    print(format_for_naver_blog(draft))
