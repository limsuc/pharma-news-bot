import logging

import feedparser

from ..config import Settings
from ..models import NewsItem
from ..text import normalize_text


logger = logging.getLogger(__name__)


class RssCollector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def collect(self) -> list[NewsItem]:
        results: list[NewsItem] = []
        for feed_url in self.settings.rss_feeds:
            feed = feedparser.parse(feed_url)
            if getattr(feed, "bozo", False):
                logger.warning("RSS parse warning for %s: %s", feed_url, getattr(feed, "bozo_exception", "unknown"))

            source = normalize_text(getattr(feed.feed, "title", "")) or "RSS"
            for entry in feed.entries[: self.settings.rss_limit_per_feed]:
                title = normalize_text(getattr(entry, "title", ""))
                link = getattr(entry, "link", "")
                if not title or not link:
                    continue
                results.append(
                    NewsItem(
                        title=title,
                        link=link,
                        source=source,
                        summary=normalize_text(getattr(entry, "summary", "")),
                        published_at=getattr(entry, "published", None),
                        meta={"feed_url": feed_url},
                    )
                )

        logger.info("Collected %s RSS news items.", len(results))
        return results

