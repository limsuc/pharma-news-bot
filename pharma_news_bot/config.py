import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str | None
    telegram_channel: str
    naver_client_id: str | None
    naver_client_secret: str | None
    max_news: int
    db_path: Path
    log_dir: Path
    telegram_retry_count: int
    telegram_retry_delay_seconds: float
    request_timeout_seconds: int
    naver_display: int
    max_article_age_days: int
    rss_limit_per_feed: int
    dailypharm_priority_bonus: int
    dry_run: bool
    bot_paused: bool
    skip_korea_holidays: bool
    trusted_rss_include_all: bool
    rss_feeds: list[str] = field(default_factory=list)
    naver_queries: list[str] = field(default_factory=list)


def _csv_env(name: str, fallback: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return fallback
    return [item.strip() for item in value.split(",") if item.strip()]


def load_settings() -> Settings:
    load_dotenv()

    default_rss = [
        "https://www.hitnews.co.kr/rss/allArticle.xml",
        "https://www.dailymedipharm.com/rss/allArticle.xml",
    ]
    default_queries = [
        "데일리팜 제약 바이오 신약 임상 급여 약가 CSO",
        "제약 바이오 신약 임상 FDA 식약처 급여 약가",
        "제약영업 CSO 리베이트 처방 병의원 제약",
        "비만치료제 GLP-1 항암제 바이오시밀러 제약",
        "국내 제약사 기술수출 허가 임상",
        "의약품 급여 등재 약가 협상 제약",
    ]

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_channel=os.getenv("TELEGRAM_CHANNEL", "@dailypharmnews"),
        naver_client_id=os.getenv("NAVER_CLIENT_ID"),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET"),
        max_news=int(os.getenv("MAX_NEWS", "12")),
        db_path=ROOT_DIR / os.getenv("DB_PATH", "sent_news.db"),
        log_dir=ROOT_DIR / os.getenv("LOG_DIR", "logs"),
        telegram_retry_count=int(os.getenv("TELEGRAM_RETRY_COUNT", "3")),
        telegram_retry_delay_seconds=float(os.getenv("TELEGRAM_RETRY_DELAY_SECONDS", "3")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
        naver_display=int(os.getenv("NAVER_DISPLAY", "50")),
        max_article_age_days=int(os.getenv("MAX_ARTICLE_AGE_DAYS", "7")),
        rss_limit_per_feed=int(os.getenv("RSS_LIMIT_PER_FEED", "30")),
        dailypharm_priority_bonus=int(os.getenv("DAILYPHARM_PRIORITY_BONUS", "8")),
        dry_run=os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes", "y"},
        bot_paused=os.getenv("BOT_PAUSED", "false").lower() in {"1", "true", "yes", "y"},
        skip_korea_holidays=os.getenv("SKIP_KOREA_HOLIDAYS", "true").lower() in {"1", "true", "yes", "y"},
        trusted_rss_include_all=os.getenv("TRUSTED_RSS_INCLUDE_ALL", "true").lower() in {"1", "true", "yes", "y"},
        rss_feeds=_csv_env("RSS_FEEDS", default_rss),
        naver_queries=_csv_env("NAVER_QUERIES", default_queries),
    )
