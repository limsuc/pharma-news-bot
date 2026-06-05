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
WATCH_TITLE_MAX_LEN = 36


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


def _compact_text(text: str, max_len: int) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -·|")
    if len(cleaned) > max_len:
        return cleaned[:max_len].rstrip() + "..."
    return cleaned


def _issue_title(item: NewsItem) -> str:
    return _compact_text(item.short_title or item.title, WATCH_TITLE_MAX_LEN)


def _article_watch_point(item: NewsItem) -> str:
    title = _issue_title(item)
    text = f"{item.title} {item.summary}".upper()

    if _has_any(text, ["AI", "인공지능"]):
        return f"‘{title}’ 이슈는 제약사 실무에 AI가 깊숙이 들어오면서 생산성 개선과 보안·고용 불안이 동시에 커지는 흐름으로 볼 수 있습니다."

    if _has_any(text, ["정부 지원", "정책금융", "펀드", "R&D", "투자"]):
        return f"‘{title}’은 정책자금이 후기 임상·백신·생산 인프라 쪽으로 이동하는 신호입니다. 관련 기업은 자금 조달과 파이프라인 속도를 같이 봐야 합니다."

    if _has_any(text, ["급여", "보험", "약가", "상한액", "등재", "RSA", "수가", "관리급여"]):
        return f"‘{title}’은 가격·급여 조건이 시장 접근성을 좌우하는 사례입니다. 처방 확대 가능성은 경쟁 품목 대비 급여 포지션에서 갈릴 수 있습니다."

    if _has_any(text, ["허가", "FDA", "식약처", "승인", "품목허가", "국내 허가"]):
        return f"‘{title}’은 허가 이후 실제 시장 진입 단계로 넘어가는 뉴스입니다. 출시 시점, 급여 여부, 기존 치료 옵션과의 차별성이 관전 포인트입니다."

    if _has_any(text, ["임상", "3상", "리얼월드", "실제 진료", "치료 혜택"]):
        return f"‘{title}’은 임상·실사용 근거가 제품 신뢰도를 보강하는 흐름입니다. 영업 현장에서는 환자군과 비교 데이터가 메시지의 핵심이 될 수 있습니다."

    if _has_any(text, ["인수", "합병", "M&A", "계약", "판권", "공급", "매각"]):
        return f"‘{title}’은 품목 포트폴리오와 경쟁 구도가 바뀔 수 있는 신호입니다. 담당 품목과 대체·경쟁 관계를 다시 확인할 필요가 있습니다."

    if _has_any(text, ["CSO", "리베이트", "영업", "마케팅", "처방", "병의원"]):
        return f"‘{title}’은 제약 영업 현장의 운영 방식과 메시지 관리에 연결되는 이슈입니다. 규제 리스크와 현장 실행 가능성을 함께 봐야 합니다."

    if _has_any(text, ["신제품", "출시", "선봬", "공급 확대", "시장", "브랜드"]):
        return f"‘{title}’은 신규 품목·브랜드 경쟁이 이어지는 흐름입니다. 실제 매출 기여는 유통 채널과 타깃 고객 반응을 확인해야 합니다."

    return f"‘{title}’은 오늘 선정 기사 중 흐름을 만들 수 있는 이슈입니다. 담당 품목·거래처와 연결되는 변화가 있는지 확인해볼 만합니다."


def build_watch_points(items: list[NewsItem]) -> list[str]:
    points: list[str] = []
    used_categories: set[str] = set()

    ranked_items = sorted(items, key=lambda item: item.score, reverse=True)

    for item in ranked_items:
        if item.category in used_categories and len(used_categories) < 3:
            continue
        point = _article_watch_point(item)
        if point not in points:
            points.append(point)
            used_categories.add(item.category)
        if len(points) >= 3:
            return points

    for item in ranked_items:
        point = _article_watch_point(item)
        if point not in points:
            points.append(point)
        if len(points) >= 3:
            return points

    if not points:
        points.append("오늘 뉴스는 개별 기사보다 흐름을 보는 쪽이 중요합니다. 담당 품목과 경쟁 품목에 연결되는 키워드를 먼저 골라보면 좋겠습니다.")

    return points


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
