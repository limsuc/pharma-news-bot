import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
TRUE_VALUES = {"1", "true", "yes", "y"}


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


def _env(name: str, fallback: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return fallback
    return value.strip()


def _int_env(name: str, fallback: int) -> int:
    return int(_env(name, str(fallback)))


def _float_env(name: str, fallback: float) -> float:
    return float(_env(name, str(fallback)))


def _bool_env(name: str, fallback: bool) -> bool:
    fallback_text = "true" if fallback else "false"
    return _env(name, fallback_text).lower() in TRUE_VALUES


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
        telegram_channel=_env("TELEGRAM_CHANNEL", "@dailypharmnews"),
        naver_client_id=os.getenv("NAVER_CLIENT_ID"),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET"),
        max_news=_int_env("MAX_NEWS", 12),
        db_path=ROOT_DIR / _env("DB_PATH", "sent_news.db"),
        log_dir=ROOT_DIR / _env("LOG_DIR", "logs"),
        telegram_retry_count=_int_env("TELEGRAM_RETRY_COUNT", 3),
        telegram_retry_delay_seconds=_float_env("TELEGRAM_RETRY_DELAY_SECONDS", 3),
        request_timeout_seconds=_int_env("REQUEST_TIMEOUT_SECONDS", 15),
        naver_display=_int_env("NAVER_DISPLAY", 50),
        max_article_age_days=_int_env("MAX_ARTICLE_AGE_DAYS", 7),
        rss_limit_per_feed=_int_env("RSS_LIMIT_PER_FEED", 30),
        dailypharm_priority_bonus=_int_env("DAILYPHARM_PRIORITY_BONUS", 8),
        dry_run=_bool_env("DRY_RUN", False),
        bot_paused=_bool_env("BOT_PAUSED", False),
        skip_korea_holidays=_bool_env("SKIP_KOREA_HOLIDAYS", True),
        trusted_rss_include_all=_bool_env("TRUSTED_RSS_INCLUDE_ALL", True),
        rss_feeds=_csv_env("RSS_FEEDS", default_rss),
        naver_queries=_csv_env("NAVER_QUERIES", default_queries),
    )
