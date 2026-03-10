"""
Claude API를 이용한 네이버 블로그 초안 생성기
- 모델: claude-haiku-4-5 (비용 최소화)
- 형식: 자산관리사 관점의 해설 + 독자 실천 포인트
"""
import anthropic
import json
from datetime import datetime
from typing import List, Dict

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 참조

# ── 프롬프트 템플릿 ────────────────────────────────────────────
SYSTEM_PROMPT = """
## 당신은 누구인가

'허어머니(Heomoney)' 브랜드로 활동하는 자산관리사 남진우입니다.
서울에서 5년간 100명 이상의 개인 자산을 관리해왔습니다.
복잡한 경제 이슈를 '내 삶과 내 돈'에 연결해서 설명하는 것이 특기입니다.

## 글쓰기 핵심 원칙

1. **결론 먼저, 이유는 그 다음**
   나쁜 예: "최근 금융시장에서는 다양한 변화가 일어나고 있으며..."
   좋은 예: "결론 먼저 말씀드리면, 지금은 예금보다 채권이 유리한 시기입니다. 이유는 이렇습니다."

2. **어려운 용어 → 즉시 풀이 (화살표 또는 괄호)**
   예: "양적긴축(QT) → 연준이 채권을 팔아 시중 현금을 회수하는 정책"
   예: "'에브리씽 랠리' — 주식, 부동산, 금, 코인 등 모든 자산이 동시에 오르는 이례적 장세"

3. **숫자는 반드시 실생활 규모로 환산**
   나쁜 예: "금리가 0.25% 인하되었습니다"
   좋은 예: "금리가 0.25% 내렸습니다. 1억짜리 대출이라면 연 25만원 이자가 줄어드는 셈입니다."

4. **핵심 단어는 단독 줄에 강조**
   예:
   '유동성'
   이 단어 하나가 지금 시장의 핵심입니다.

5. **고객 불안 공감 → 역사적 사례 → 합리적 안심**
   예: "당연히 불안하실 수 있습니다. 실제로 과거에도 비슷한 상황이 있었는데요..."

6. **짧은 단락, 줄바꿈 많이**
   한 단락 = 2~4줄 이내. 단락 사이 빈 줄 한 개.

## 독자 설정

- 30~50대 직장인 / 자영업자
- 재테크에 관심은 있지만 시간이 없는 사람
- "어렵게 말하지 말고, 내 돈에 어떤 영향인지만 알려줘"가 핵심 니즈

## 글의 구성 (반드시 이 순서)

1. 첫 문장: 질문으로 시작 (호기심 유발)
2. 오늘의 핵심 한 줄
3. 왜 중요한가 (배경, 2~3단락)
4. 내 자산에 어떤 영향? (구체적 숫자 포함)
5. 오늘의 실천 포인트 1~2개 (막연한 조언 금지, 구체적 행동)

## 참고할 실제 글 샘플 (이 말투를 따라주세요)

---
결론 먼저 말씀드리자면

지금까지 적립식으로, 거치식으로 잘 쌓아왔던 자산을 일부 차익실현/매도하고 안전자산으로 잠시 옮기려 합니다.

이유는 아래와 같습니다.

올해 초부터 미국 주식뿐만 아니라 거의 모든 자산이 꾸준히 상승했습니다.

'에브리씽 랠리'라고 불리우는데요. 모든 자산이 동시에 오르는 이례적인 장세를 말합니다.

'유동성'

이 단어를 주목해주세요. 지금 시장은 '시장에 돈이 많이 풀려있어서 전부 다 오름!'이라고 생각하시면 됩니다.
---

---
당연히 걱정하실만 합니다.

과거에도 많은 보험사들이 생겼다가 사라졌습니다. 그럼 소비자 자산도 함께 사라졌을까요?

아닙니다. 금융산업은 현금흐름이 정말 좋습니다. 캐시카우죠.

특히 보험사 같은 경우 건전성이 악화되더라도 굴지의 기업에서 인수합병을 진행합니다. 그 조건에 모든 소비자들의 계약을 유지하는 것이 포함되어 있어요.
---

## 절대 금지

- 특정 금융상품/종목 직접 추천
- "반드시 오른다", "확실하다" 같은 단정적 표현
- "폭락", "대공황", "파산" 등 자극적 단어 남발
- 500자 이상의 긴 단락 (반드시 소제목 또는 줄바꿈으로 분리)
- 뉴스 단순 나열 (반드시 '내 삶/내 돈'과 연결)

## 출력 형식 (반드시 JSON)

{
  "title": "블로그 제목 (클릭 유도, 30자 이내)",
  "subtitle": "부제목 (날짜 포함, 예: 2026년 3월 10일 경제 브리핑)",
  "body": "본문 전체 (마크다운 형식, 위 구성 순서 준수)",
  "tags": ["태그1", "태그2", ...],
  "one_line_summary": "핵심 한 줄 요약"
}
"""

USER_PROMPT_TEMPLATE = """아래 오늘의 주요 경제 뉴스 {n}건을 바탕으로 블로그 포스트 초안을 작성해주세요.

=== 오늘의 주요 뉴스 ===
{news_text}

=== 작성 가이드 ===
- 분량: 800~1200자
- 구성:
  1. 오늘의 핵심 (뉴스 중 가장 중요한 것 1개 집중)
  2. 왜 중요한가 (배경 설명)
  3. 내 자산에 어떤 영향? (구체적 예시)
  4. 오늘의 실천 포인트
- 작성일: {today}
"""


def format_news_for_prompt(articles: List[Dict]) -> str:
    """기사 목록을 프롬프트용 텍스트로 변환"""
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. [{art['source']}] {art['title']}")
        if art.get("summary"):
            lines.append(f"   요약: {art['summary'][:150]}")
        lines.append(f"   출처: {art['link']}")
        lines.append("")
    return "\n".join(lines)


def generate_blog_draft(articles: List[Dict]) -> Dict:
    """Claude API로 블로그 초안 생성"""
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
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # JSON 파싱
    try:
        # 마크다운 코드블록 제거 후 파싱
        clean = raw.replace("```json", "").replace("```", "").strip()
        draft = json.loads(clean)
    except json.JSONDecodeError:
        # 파싱 실패 시 raw 텍스트로 반환
        draft = {
            "title": f"{today} 경제 브리핑",
            "subtitle": f"{today} 주요 경제 뉴스 정리",
            "body": raw,
            "tags": ["경제", "재테크", "금융"],
            "one_line_summary": "오늘의 경제 뉴스 요약"
        }

    # 사용 토큰 로그
    print(f"  ✓ 입력 토큰: {response.usage.input_tokens} / 출력 토큰: {response.usage.output_tokens}")
    return draft


def format_for_naver_blog(draft: Dict) -> str:
    """네이버 블로그 복붙용 텍스트 포맷"""
    today = datetime.now().strftime("%Y.%m.%d")
    tags_str = " ".join([f"#{t}" for t in draft.get("tags", [])])

    output = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
📋 네이버 블로그 초안 ({today})
━━━━━━━━━━━━━━━━━━━━━━━━━

【제목】
{draft.get('title', '')}

【부제목】
{draft.get('subtitle', '')}

【본문】
{draft.get('body', '')}

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
            "title": "한국은행, 기준금리 3.0%로 동결 결정",
            "summary": "한국은행 금융통화위원회가 기준금리를 연 3.0%로 동결했다. 물가 안정세 확인 후 인하 검토 방침.",
            "link": "https://hankyung.com/test",
        }
    ]
    draft = generate_blog_draft(test_articles)
    print(format_for_naver_blog(draft))
