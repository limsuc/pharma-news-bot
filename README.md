# Pharma News Bot

제약/바이오 뉴스를 네이버 뉴스 API와 RSS에서 수집해 중복 제거, 카테고리 분류, 텔레그램 채널 발송까지 자동화하는 운영형 봇입니다.

## 주요 기능

- 네이버 뉴스 API + RSS 혼합 수집
- 데일리팜 관련 기사 우선순위 강화
- SQLite 기반 발송 이력 저장 및 중복 제거
- 급여/약가, 임상/허가, CSO/영업, 시장/품목, 기업/투자 분류
- 제약영업/CSO 관점 태깅
- 텔레그램 발송 실패 재시도
- 토/일 및 대한민국 공휴일 발송 제외
- 오류 로그 파일 및 SQLite `error_logs` 저장
- GitHub Actions 매일 자동 실행
- `.env`는 로컬 전용, GitHub에서는 Actions Secrets 사용

## 구조

```txt
pharma-news-bot/
  main.py
  pharma_news_bot/
    collectors/
      naver.py
      rss.py
    classifier.py
    config.py
    dedupe.py
    logging_setup.py
    message.py
    models.py
    pipeline.py
    storage.py
    telegram.py
    text.py
  .github/workflows/daily-news.yml
  .env.example
  requirements.txt
  run_windows.bat
```

## 설치

```bash
pip install -r requirements.txt
copy .env.example .env
```

`.env`에 아래 값을 설정합니다.

```txt
TELEGRAM_BOT_TOKEN=BotFather에서 받은 토큰
TELEGRAM_CHANNEL=@dailypharmnews
NAVER_CLIENT_ID=네이버 개발자센터 Client ID
NAVER_CLIENT_SECRET=네이버 개발자센터 Client Secret
MAX_NEWS=12
```

## 실행

```bash
python main.py
```

발송 없이 메시지와 파이프라인만 확인하려면 `.env`에 `DRY_RUN=true`를 넣고 실행합니다.

## GitHub Actions 설정

GitHub 저장소의 `Settings > Secrets and variables > Actions`에 아래 secrets를 등록합니다.

- `TELEGRAM_BOT_TOKEN`
- `NAVER_CLIENT_ID`
- `NAVER_CLIENT_SECRET`

기본 스케줄은 한국시간 월-금 오전 8시입니다. 봇 실행일이 대한민국 공휴일이면 수집/발송하지 않고 종료합니다. SQLite 발송 이력은 GitHub Actions cache로 복원하고, 로그와 DB는 artifact로 업로드합니다.

## 운영 설정

`.env.example`에 모든 설정 키가 있습니다.

- `DAILYPHARM_PRIORITY_BONUS`: 데일리팜 관련 기사 가중치
- `TELEGRAM_RETRY_COUNT`: 발송 재시도 횟수
- `BOT_PAUSED`: `true`이면 수집/발송 없이 종료
- `SKIP_KOREA_HOLIDAYS`: 대한민국 공휴일 발송 제외 여부
- `TRUSTED_RSS_INCLUDE_ALL`: 등록된 RSS 피드를 신뢰하고 키워드가 약해도 후보에 포함할지 여부
- `MAX_ARTICLE_AGE_DAYS`: 발행일 기준 최근 기사만 포함할 기간
- `RSS_FEEDS`: 쉼표로 구분한 RSS URL 목록
- `NAVER_QUERIES`: 쉼표로 구분한 네이버 검색어 목록
- `DB_PATH`: SQLite DB 경로
- `LOG_DIR`: 오류/운영 로그 디렉터리
