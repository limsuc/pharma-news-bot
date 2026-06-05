import logging
import re
import time
from html import unescape
from urllib.parse import quote

import requests

from ..config import Settings
from ..models import NewsItem
from ..text import normalize_text


logger = logging.getLogger(__name__)

BASE_URL = "https://www.dailypharm.com"
NEWS_LINK_RE = re.compile(r"https://www\.dailypharm\.com/user/news/\d+")
META_RE_TEMPLATE = r'<meta\s+(?:name|property)="{name}"\s+content="([^"]*)"'
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
SUMMARY_MAX_LEN = 140


class DailyPharmCollector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (compatible; PharmaNewsBot/1.0; +https://github.com/limsuc/pharma-news-bot)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

    def collect(self) -> list[NewsItem]:
        if not self.settings.dailypharm_enabled:
            logger.info("DailyPharm collection is disabled.")
            return []

        links = self._collect_links()
        results: list[NewsItem] = []

        for link in links[: self.settings.dailypharm_limit]:
            item = self._fetch_article_meta(link)
            if item:
                results.append(item)
            time.sleep(0.2)

        logger.info("Collected %s DailyPharm news items.", len(results))
        return results

    def _collect_links(self) -> list[str]:
        urls = [
            f"{BASE_URL}/user/news?group={quote('제약·바이오')}",
            BASE_URL,
        ]
        links: list[str] = []
        seen: set[str] = set()

        for url in urls:
            try:
                response = self.session.get(url, timeout=self.settings.request_timeout_seconds)
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("DailyPharm list fetch failed. url=%s error=%s", url, exc)
                continue

            for match in NEWS_LINK_RE.finditer(response.text):
                link = match.group(0)
                if link not in seen:
                    seen.add(link)
                    links.append(link)

        return links

    def _fetch_article_meta(self, link: str) -> NewsItem | None:
        try:
            response = self.session.get(link, timeout=self.settings.request_timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("DailyPharm article fetch failed. link=%s error=%s", link, exc)
            return None

        html = response.text
        title = self._meta(html, "og:title") or self._title(html)
        summary = self._meta(html, "description") or self._meta(html, "og:description")
        title = self._clean_title(title)
        summary = self._clean_summary(summary)

        if not title:
            return None

        return NewsItem(
            title=title,
            link=link,
            source="데일리팜",
            summary=summary,
            published_at=None,
            meta={"collector": "dailypharm"},
        )

    def _meta(self, html: str, name: str) -> str:
        pattern = re.compile(META_RE_TEMPLATE.format(name=re.escape(name)), re.IGNORECASE | re.DOTALL)
        match = pattern.search(html)
        return normalize_text(unescape(match.group(1))) if match else ""

    def _title(self, html: str) -> str:
        match = TITLE_RE.search(html)
        return normalize_text(unescape(match.group(1))) if match else ""

    def _clean_title(self, title: str) -> str:
        title = normalize_text(title)
        title = re.sub(r"^\[?데일리팜\]?", "", title).strip()
        return title

    def _clean_summary(self, summary: str) -> str:
        summary = normalize_text(summary)
        if len(summary) > SUMMARY_MAX_LEN:
            summary = summary[:SUMMARY_MAX_LEN].rstrip() + "..."
        return summary
