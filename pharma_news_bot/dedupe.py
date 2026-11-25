from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
import re

from .classifier import BASE_KEYWORDS, CATEGORY_ORDER, classify
from .models import NewsItem
from .storage import NewsStore
from .text import article_id, canonical_link, normalize_text, shorten_title, title_key


SECTION_LIMIT = 3
KST = timezone(timedelta(hours=9))
NEAR_DUPLICATE_THRESHOLD = 0.58
STOPWORDS = {
    "제약", "바이오", "뉴스", "단독", "속보", "종합", "기자", "오늘",
    "국내", "글로벌", "관련", "통해", "한다", "했다", "된다", "위해", "대한",
}


def is_relevant(item: NewsItem) -> bool:
    haystack = f"{item.title} {item.summary}".lower()
    return any(keyword.lower() in haystack for keyword in BASE_KEYWORDS)


def _pick_by_section(items: list[NewsItem], max_news: int) -> list[NewsItem]:
    selected: list[NewsItem] = []
    sections = [[item for item in items if item.category == category] for category in CATEGORY_ORDER]
    for index in range(SECTION_LIMIT):
        for section in sections:
            if len(selected) >= max_news:
                return selected
            if index < len(section):
                selected.append(section[index])
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


def _tokens(text: str) -> set[str]:
    text = normalize_text(text)
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", text.lower())
    tokens = [re.sub(r"(에서는|에서|으로|은|는|을|를|의|와|과)$", "", token)
              if len(token) >= 4 else token for token in tokens]
    return {token for token in tokens if len(token) > 1 and token not in STOPWORDS}


def _title_bigrams(title: str) -> set[str]:
    key = title_key(title)
    return {key[index:index + 2] for index in range(len(key) - 1)}


def _same_story(left: NewsItem, right: NewsItem) -> bool:
    left_title, right_title = _tokens(left.title), _tokens(right.title)
    shared = left_title & right_title
    # An otherwise identical headline with a different entity is a separate story.
    if len(left_title - right_title) == len(right_title - left_title) == 1:
        return False
    left_grams, right_grams = _title_bigrams(left.title), _title_bigrams(right.title)
    total = len(left_grams) + len(right_grams)
    title_similarity = 2 * len(left_grams & right_grams) / total if total else 0.0
    # Keep different trial phases and numerical results as potential updates.
    left_numbers = set(re.findall(r"\d+(?:\.\d+)?", left.title))
    right_numbers = set(re.findall(r"\d+(?:\.\d+)?", right.title))
    if left_numbers and right_numbers and left_numbers != right_numbers:
        return False
    if len(shared) >= 2 and title_similarity >= 0.65:
        return True
    anchors = shared - {"제약사", "임상", "허가", "승인", "신약", "발표", "결과", "개발", "출시"}
    if len(anchors) >= 2 and len(shared) >= 3 and title_similarity >= 0.35:
        return True
    # Short summaries and Korean particles can dilute whole-article Jaccard overlap.
    left_text = _tokens(f"{left.title} {left.summary}")
    right_text = _tokens(f"{right.title} {right.summary}")
    if _similarity(left_text, right_text) >= NEAR_DUPLICATE_THRESHOLD:
        return True
    shorter = min(len(left_text), len(right_text))
    overlap = len(left_text & right_text) / shorter if shorter else 0.0
    return len(shared) >= 2 and title_similarity >= 0.45 and overlap >= 0.45


def _similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    if intersection < 3:
        return 0.0
    union = len(left | right)
    return intersection / union


def _remove_near_duplicates(items: list[NewsItem]) -> list[NewsItem]:
    selected: list[NewsItem] = []
    for item in items:
        if any(_same_story(item, seen) for seen in selected):
            continue
        selected.append(item)
    return selected


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
    candidates = _remove_near_duplicates(candidates)
    return _pick_by_section(candidates, max_news)
