from dataclasses import dataclass, field


@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    summary: str = ""
    published_at: str | None = None
    id: str = ""
    short_title: str = ""
    category: str = ""
    audience: str = ""
    score: int = 0
    meta: dict[str, str] = field(default_factory=dict)

