import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .models import NewsItem


KST = timezone(timedelta(hours=9))
logger = logging.getLogger(__name__)


class NewsStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_news (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    source TEXT,
                    category TEXT,
                    audience TEXT,
                    score INTEGER DEFAULT 0,
                    sent_at TEXT NOT NULL
                )
                """
            )
            self._migrate_sent_news(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sent_news_sent_at ON sent_news(sent_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at)")

    def _migrate_sent_news(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(sent_news)").fetchall()}
        migrations = {
            "source": "ALTER TABLE sent_news ADD COLUMN source TEXT",
            "category": "ALTER TABLE sent_news ADD COLUMN category TEXT",
            "audience": "ALTER TABLE sent_news ADD COLUMN audience TEXT",
            "score": "ALTER TABLE sent_news ADD COLUMN score INTEGER DEFAULT 0",
        }
        for column, sql in migrations.items():
            if column not in columns:
                conn.execute(sql)

    def already_sent(self, news_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM sent_news WHERE id = ?", (news_id,)).fetchone()
            return row is not None

    def mark_sent(self, items: Iterable[NewsItem]) -> None:
        now = datetime.now(KST).isoformat()
        rows = [
            (item.id, item.title, item.link, item.source, item.category, item.audience, item.score, now)
            for item in items
        ]
        if not rows:
            return
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO sent_news
                (id, title, link, source, category, audience, score, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def log_error(self, stage: str, message: str, context: str = "") -> None:
        logger.error("%s: %s %s", stage, message, context)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO error_logs (stage, message, context, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (stage, message, context, datetime.now(KST).isoformat()),
            )
