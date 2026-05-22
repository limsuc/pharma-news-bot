from .classifier import BASE_KEYWORDS, CATEGORY_ORDER, classify
from .models import NewsItem
from .storage import NewsStore
from .text import article_id, canonical_link, shorten_title, title_key
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone


SECTION_LIMIT = 3
KST = timezone(timedelta(hours=9))


def is_relevant(item: NewsItem) -> bool:
    haystack = f"{item.title} {item.summary}".lower()
    return any(keyword.lower() in haystack for keyword in BASE_KEYWORDS)


def _pick_by_section(items: list[NewsItem], max_news: int) -> list[NewsItem]:
    selected: list[NewsItem] = []
    selected_ids: set[str] = set()

    for category in CATEGORY_ORDER:
        category_items = [item for item in items if item.category == category]
        for item in category_items[:SECTION_LIMIT]:
            if len(selected) >= max_news:
                return selected
            selected.append(item)
            selected_ids.add(item.id)

    if len(selected) >= max_news:
        return selected

    for item in items:
        if item.id in selected_ids:
            continue
        selected.append(item)
        if len(selected) >= max_news:
            break

    return selected


def _published_datetime(item: NewsItem) -> datetime | None:
    if not item.published_at:
        return None
    try:
        parsed = parsedate_to_datetime(item.published_at)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=KST)
        return parsed
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def _is_recent(item: NewsItem, max_article_age_days: int) -> bool:
    if max_article_age_days <= 0:
        return True
    published = _published_datetime(item)
    if published is None:
        return True
    cutoff = datetime.now(KST) - timedelta(days=max_article_age_days)
    return published.astimezone(KST) >= cutoff


def dedupe_rank(
    items: list[NewsItem],
    store: NewsStore,
    max_news: int,
    dailypharm_bonus: int,
    trusted_rss_include_all: bool,
    max_article_age_days: int,
) -> list[NewsItem]:
    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    candidates: list[NewsItem] = []

    for item in items:
        if not _is_recent(item, max_article_age_days):
            continue

        trusted_rss_item = trusted_rss_include_all and item.source != "Naver News"
        if not trusted_rss_item and not is_relevant(item):
            continue

        link_key = canonical_link(item.link)
        name_key = title_key(item.title)
        if link_key in seen_links or name_key in seen_titles:
            continue

        item.id = article_id(item.title, item.link)
        if store.already_sent(item.id):
            continue

        item.short_title = shorten_title(item.title)
        classify(item, dailypharm_bonus)

        seen_links.add(link_key)
        seen_titles.add(name_key)
        candidates.append(item)

    candidates.sort(key=lambda item: item.score, reverse=True)
    return _pick_by_section(candidates, max_news)
