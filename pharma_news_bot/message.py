import html
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .classifier import CATEGORY_ORDER
from .models import NewsItem


KST = timezone(timedelta(hours=9))
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
SECTION_LIMIT = 3
PREVIEW_MAX_LEN = 115


KEYWORD_RULES = [
    ("#CSO규제", ["CSO", "리베이트", "영업대행", "꼼수"]),
    ("#리베이트", ["리베이트"]),
    ("#약가", ["약가", "급여", "보험", "상한액", "등재", "RSA"]),
    ("#GLP1", ["GLP-1", "GLP1", "비만치료제", "세마글루타이드"]),
    ("#기술수출", ["기술수출", "라이선스", "판권"]),
    ("#임상", ["임상", "3상", "FDA", "허가", "식약처"]),
    ("#바이오시밀러", ["바이오시밀러", "시밀러"]),
    ("#MNA", ["M&A", "인수", "합병"]),
]


def today_label() -> str:
    now = datetime.now(KST)
    return f"{now:%Y.%m.%d} ({WEEKDAYS[now.weekday()]})"


def _has_any(text: str, keywords: list[str]) -> bool:
    upper = text.upper()
    return any(keyword.upper() in upper for keyword in keywords)


def _all_text(items: list[NewsItem]) -> str:
    return " ".join(f"{item.title} {item.summary} {item.category}" for item in items)


def _preview_text(item: NewsItem) -> str:
    preview = item.summary or ""
    preview = re.sub(r"<[^>]+>", "", preview)
    preview = re.sub(r"\s+", " ", preview).strip()
    if not preview:
        return ""
    if len(preview) > PREVIEW_MAX_LEN:
        preview = preview[:PREVIEW_MAX_LEN].rstrip() + "..."
    return preview


def build_watch_points(items: list[NewsItem]) -> list[str]:
    text = _all_text(items)
    points: list[str] = []

    if _has_any(text, ["CSO", "리베이트", "영업대행", "꼼수"]):
        points.append("CSO 규제와 리베이트 이슈가 다시 전면에 올라왔습니다. 영업대행 구조를 쓰는 회사들은 당분간 메시지 관리가 중요해 보입니다.")

    if _has_any(text, ["비만", "GLP-1", "GLP1", "바이오시밀러", "시밀러", "항암", "복합제"]):
        points.append("비만치료제·바이오시밀러·신규 품목 뉴스가 이어지고 있습니다. 시장은 효능뿐 아니라 투약 편의성과 가격 경쟁력으로 움직이는 분위기입니다.")

    if _has_any(text, ["급여", "보험", "약가", "상한액", "등재", "RSA", "협상"]):
        points.append("급여와 약가 이슈는 처방 확대 속도를 좌우할 수 있습니다. 경쟁 품목과 비교할 때 가격 포지션을 함께 봐야 합니다.")

    if _has_any(text, ["임상", "허가", "FDA", "식약처", "기술수출", "3상"]):
        points.append("기술수출·허가·임상 진전 뉴스는 긍정적이지만, 실제 영업 기회는 급여 등재와 출시 타이밍에서 갈릴 가능성이 큽니다.")

    if _has_any(text, ["인수", "합병", "M&A", "R&D", "기술도입", "계약"]):
        points.append("인수·합병·기술도입 기사는 제품 라인업 재편 신호일 수 있습니다. 담당 품목의 경쟁 구도 변화를 같이 확인할 필요가 있습니다.")

    if not points:
        points.append("오늘 뉴스는 개별 기사보다 흐름을 보는 쪽이 중요합니다. 담당 품목과 경쟁 품목에 연결되는 키워드를 먼저 골라보면 좋겠습니다.")

    return points[:3]


def build_today_keywords(items: list[NewsItem]) -> list[str]:
    text = _all_text(items)
    keywords = [tag for tag, rule_keywords in KEYWORD_RULES if _has_any(text, rule_keywords)]
    if not keywords:
        return ["#제약", "#바이오", "#영업전략"]
    return keywords[:6]


def build_message(items: list[NewsItem]) -> str:
    if not items:
        return (
            "📰 <b>오늘의 제약·바이오 뉴스</b>\n"
            f"{today_label()}\n\n"
            "새로 발송할 뉴스가 없습니다."
        )

    grouped: dict[str, list[NewsItem]] = defaultdict(list)
    for item in items:
        grouped[item.category].append(item)

    lines = [
        "📰 <b>오늘의 제약·바이오 뉴스</b>",
        today_label(),
        "",
    ]

    for category in CATEGORY_ORDER:
        lines.append(f"<b>{html.escape(category)}</b>")
        for item in grouped.get(category, [])[:SECTION_LIMIT]:
            title = html.escape(item.short_title or item.title)
            link = html.escape(item.link)
            lines.append(f'• <b><a href="{link}">{title}</a></b>')
            preview = _preview_text(item)
            if preview:
                lines.append(f"<blockquote>{html.escape(preview)}</blockquote>")
        if not grouped.get(category):
            lines.append("• 오늘 선별된 뉴스 없음")
        lines.append("")

    lines.append("👀 <b>오늘의 관전 포인트</b>")
    for point in build_watch_points(items):
        lines.append(f"• {html.escape(point)}")

    lines.extend(
        [
            "",
            "🏷 <b>오늘의 키워드</b>",
            " ".join(build_today_keywords(items)),
            "",
            "🔎 <b>뉴스 더 보기</b>",
            '<a href="https://search.naver.com/search.naver?where=news&amp;query=%EC%A0%9C%EC%95%BD%20%EB%B0%94%EC%9D%B4%EC%98%A4">네이버 뉴스</a> · <a href="https://www.dailypharm.com/">데일리팜</a>',
            "",
            "#제약 #바이오 #데일리팜 #CSO #제약영업",
        ]
    )
    return "\n".join(lines)
