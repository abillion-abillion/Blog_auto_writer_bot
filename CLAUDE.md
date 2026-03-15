# Blog Auto Writer Bot — Claude Code 컨텍스트

## 프로젝트 한 줄 요약
경제 뉴스 RSS를 수집 → Claude API로 네이버 블로그 초안 생성 → 텔레그램으로 전송하는 자동화 봇

---

## 디렉토리 구조

```
blog_auto_writer_bot/
├── CLAUDE.md                  ← 이 파일 (Claude Code 컨텍스트)
├── blog_draft.py              ← 메인 실행 파일
├── sources/
│   └── rss_collector.py       ← RSS 뉴스 수집 + 기사 선별
├── generator/
│   └── claude_writer.py       ← Claude API 초안 생성 + 포맷 변환
├── sender/
│   └── telegram_sender.py     ← 텔레그램 전송 (자동 분할)
└── .github/workflows/
    └── blog_bot.yml           ← GitHub Actions 스케줄 (매일 UTC 22:00)
```

---

## 실행 방법

### 로컬 실행
```bash
# 1. 의존성 설치
pip install anthropic feedparser requests

# 2. 환경변수 설정
export ANTHROPIC_API_KEY=sk-ant-...
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...

# 3. 실행
python blog_draft.py
```

### 단위 테스트 (모듈별 개별 실행)
```bash
# 뉴스 수집만 테스트
python sources/rss_collector.py

# 블로그 초안 생성만 테스트 (더미 기사 사용)
python generator/claude_writer.py

# 텔레그램 전송만 테스트
python sender/telegram_sender.py
```

---

## 환경변수 목록

| 변수명 | 설명 | 필수 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 | ✅ |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | ✅ |
| `TELEGRAM_CHAT_ID` | 전송 대상 채팅 ID | ✅ |

GitHub Actions에서는 Settings → Secrets에 등록:
- `ANTHROPIC_API_KEY`
- `BLOG_BOT_TOKEN` (TELEGRAM_BOT_TOKEN에 매핑)
- `BLOG_BOT_CHAT_ID` (TELEGRAM_CHAT_ID에 매핑)

---

## 각 모듈 역할 및 수정 포인트

### sources/rss_collector.py
- `RSS_SOURCES` 딕셔너리에 소스 추가/제거
- `select_top_articles()` 의 `PRIORITY_KEYWORDS` 리스트로 우선순위 키워드 조정
- `hours_back` 파라미터로 수집 시간 범위 조정 (기본 24시간)

### generator/claude_writer.py
- `SYSTEM_PROMPT`: 작성자 페르소나, 글쓰기 원칙, 출력 형식 정의
- `USER_PROMPT_TEMPLATE`: 매 실행마다 넘기는 뉴스 + 작성 지시
- `get_placeholder_images()`: picsum.photos 기반 이미지 URL 생성 (API 키 불필요)
- `clean_body()`: 마크다운 기호 제거 + 줄바꿈 정리
- 모델: `claude-haiku-4-5-20251001` (비용 최소화 목적)

### sender/telegram_sender.py
- 3800자 초과 시 자동 분할 전송
- `send_long_text()`: 문단 경계(\n\n)에서 자르기
- `parse_mode="HTML"` 사용 중 → 본문에 HTML 특수문자(<, >, &) 주의

---

## 출력 데이터 흐름

```
RSS 수집 (6개 소스)
    ↓
기사 선별 (키워드 스코어링, 상위 5건)
    ↓
Claude API 호출 (JSON 응답)
    {title, subtitle, body, tags, one_line_summary, image_keywords}
    ↓
format_for_naver_blog() 변환
    - 마크다운 기호 제거
    - 이미지 URL 생성 (picsum.photos)
    - 네이버 블로그 복붙용 텍스트 완성
    ↓
텔레그램 전송 (자동 분할)
```

---

## 자주 하는 수정 작업

### RSS 소스 추가
`sources/rss_collector.py` 의 `RSS_SOURCES` 딕셔너리에 추가:
```python
"소스이름": "https://example.com/rss",
```

### 글 분량 조정
`generator/claude_writer.py` 의 `USER_PROMPT_TEMPLATE` 에서:
```
- 분량: 2000~3000자  ← 이 숫자 변경
```
`max_tokens=4000` 도 함께 조정 필요.

### 전송 채팅 변경
`sender/telegram_sender.py` 의 `TELEGRAM_CHAT_ID` 환경변수값 변경.

### 실행 스케줄 변경
`.github/workflows/blog_bot.yml` 의 cron 표현식 수정:
```yaml
- cron: "0 22 * * *"  # UTC 기준. 한국시간 = UTC+9
# 한국시간 오전 7시 발송 원하면: "0 22 * * *" (전날 UTC 22시)
```

---

## 주의사항

- `clean_body()` 는 `**굵게**`, `*이탤릭*`, `##헤더` 등 마크다운을 모두 제거함
- Claude가 JSON 대신 plain text를 반환하면 `json.JSONDecodeError` 처리로 fallback
- picsum.photos URL은 seed 값이 같으면 항상 같은 이미지 반환 (키워드 해시 기반)
- 텔레그램 `parse_mode=HTML` 사용 중이므로 본문에 `<`, `>`, `&` 문자가 있으면 깨질 수 있음
