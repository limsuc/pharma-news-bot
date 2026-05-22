import hashlib
import html
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_text(text: str | None) -> str:
    cleaned = html.unescape(text or "")
    cleaned = re.sub(r"<.*?>", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def canonical_link(link: str) -> str:
    parsed = urlsplit(link or "")
    tracking_prefixes = ("utm_",)
    tracking_keys = {"fbclid", "gclid", "yclid", "nclid"}
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in tracking_keys and not key.startswith(tracking_prefixes)
    ]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), urlencode(query), ""))


def article_id(title: str, link: str) -> str:
    raw = canonical_link(link) or normalize_text(title)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def title_key(title: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", normalize_text(title)).lower()


def shorten_title(title: str, max_len: int = 42) -> str:
    cleaned = normalize_text(title)
    cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
    for word in ["단독", "속보", "종합", "인터뷰", "기획"]:
        cleaned = cleaned.replace(f"[{word}]", "").replace(word, "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_|")
    if len(cleaned) > max_len:
        return cleaned[:max_len].rstrip() + "..."
    return cleaned
