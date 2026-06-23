import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from ..config import Settings
from ..models import NewsItem
from ..text import normalize_text


logger = logging.getLogger(__name__)


class NaverNewsCollector:
    def __init__(self, settings: Settings):
        self.settings = settings

    def collect(self) -> list[NewsItem]:
        if not self.settings.naver_client_id or not self.settings.naver_client_secret:
            logger.warning("Naver API credentials are not configured. Skipping Naver collection.")
            return []

        results: list[NewsItem] = []

        for query in self.settings.naver_queries:
            query_count = 0
            params = urllib.parse.urlencode(
                {
                    "query": query,
                    "display": self.settings.naver_display,
                    "sort": "date",
                }
            )
            url = f"https://openapi.naver.com/v1/search/news.json?{params}"
            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id", self.settings.naver_client_id)
            request.add_header("X-Naver-Client-Secret", self.settings.naver_client_secret)

            try:
                with urllib.request.urlopen(request, timeout=self.settings.request_timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                for raw in payload.get("items", []):
                    title = normalize_text(raw.get("title"))
                    link = raw.get("originallink") or raw.get("link")
                    if not title or not link:
                        continue
                    results.append(
                        NewsItem(
                            title=title,
                            link=link,
                            source="Naver News",
                            summary=normalize_text(raw.get("description")),
                            published_at=raw.get("pubDate"),
                            meta={"query": query},
                        )
                    )
                    query_count += 1
                logger.info("Collected %s Naver news items for query=%s.", query_count, query)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                logger.warning("Naver query failed. query=%s status=%s detail=%s", query, exc.code, detail)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                logger.warning("Naver query failed. query=%s error=%s", query, exc)

        logger.info("Collected %s Naver news items.", len(results))
        return results
