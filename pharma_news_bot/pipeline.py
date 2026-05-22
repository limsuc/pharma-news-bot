import logging

from .calendar import is_korea_public_holiday, today_kst_date
from .collectors.naver import NaverNewsCollector
from .collectors.rss import RssCollector
from .config import Settings
from .dedupe import dedupe_rank
from .message import build_message
from .storage import NewsStore
from .telegram import TelegramSender


logger = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = NewsStore(settings.db_path)

    def run(self) -> int:
        self.store.init()

        if self.settings.bot_paused:
            logger.info("Bot is paused by BOT_PAUSED=true. Skipping collection and Telegram send.")
            return 0

        if self.settings.skip_korea_holidays:
            is_holiday, holiday_name = is_korea_public_holiday()
            if is_holiday:
                logger.info(
                    "Skipping Telegram send because %s is a Korea public holiday: %s",
                    today_kst_date(),
                    holiday_name,
                )
                return 0

        items = []
        collectors = [
            ("naver", NaverNewsCollector(self.settings)),
            ("rss", RssCollector(self.settings)),
        ]

        for stage, collector in collectors:
            try:
                items.extend(collector.collect())
            except Exception as exc:
                self.store.log_error(stage, str(exc))

        selected = dedupe_rank(
            items,
            store=self.store,
            max_news=self.settings.max_news,
            dailypharm_bonus=self.settings.dailypharm_priority_bonus,
            trusted_rss_include_all=self.settings.trusted_rss_include_all,
            max_article_age_days=self.settings.max_article_age_days,
        )
        message = build_message(selected)

        try:
            TelegramSender(self.settings).send(message)
        except Exception as exc:
            self.store.log_error("telegram", str(exc), context=f"selected_count={len(selected)}")
            raise

        self.store.mark_sent(selected)
        logger.info("Pipeline finished. collected=%s selected=%s", len(items), len(selected))
        return len(selected)
