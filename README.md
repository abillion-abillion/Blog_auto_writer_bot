# 📝 블로그 초안 봇

경제 뉴스 RSS + 금감원/한은 공시를 수집해서
Claude API로 네이버 블로그 초안을 자동 생성하고 텔레그램으로 전송합니다.

---

## 구조

```
blog_bot/
├── blog_draft.py              # 메인 실행
├── sources/rss_collector.py   # 뉴스 수집
├── generator/claude_writer.py # 초안 생성
├── sender/telegram_sender.py  # 텔레그램 전송
└── .github/workflows/blog_bot.yml
```

---

## 설치

```bash
pip install anthropic feedparser requests
```

---

## GitHub Secrets 설정

레포 → Settings → Secrets and variables → Actions → New repository secret

| 이름 | 값 |
|------|-----|
| `ANTHROPIC_API_KEY` | sk-ant-... |
| `TELEGRAM_BOT_TOKEN` | 기존 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 기존 채팅 ID |

---

## 실행 스케줄

- **자동**: 매일 오전 7시 KST (GitHub Actions cron)
- **수동**: GitHub Actions 탭 → "블로그 초안 자동 생성" → Run workflow

---

## 흐름

```
오전 7시
  → RSS 수집 (연합뉴스, 한경, 매일경제, 서울경제, 한은, 금감원)
  → 키워드 기반 상위 5건 선별
  → Claude Haiku로 블로그 초안 생성 (800~1200자)
  → 텔레그램으로 .txt 파일 전송
  → 검토 후 네이버 블로그 복붙 발행
```

---

## 예상 비용 (월간)

| 항목 | 비용 |
|------|------|
| Claude Haiku (매일 1회) | 약 $0.5~1/월 |
| GitHub Actions | 무료 (월 2,000분) |
| 텔레그램 봇 | 무료 |

---

## 로컬 테스트

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

python blog_bot/blog_draft.py
```
