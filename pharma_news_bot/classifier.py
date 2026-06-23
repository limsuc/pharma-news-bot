import re

from .models import NewsItem


CATEGORY_ORDER = [
    "급여/보험/약가",
    "시장/품목",
    "임상/허가",
    "CSO/영업",
]

CLASSIFICATION_ORDER = [
    "급여/보험/약가",
    "임상/허가",
    "CSO/영업",
    "시장/품목",
]

CATEGORY_KEYWORDS = {
    "급여/보험/약가": ["급여", "보험", "약가", "건보", "심평원", "등재", "상한액", "RSA", "협상"],
    "시장/품목": ["시장", "품목", "비만", "GLP-1", "항암", "바이오시밀러", "당뇨", "백신", "성장호르몬"],
    "임상/허가": ["FDA", "EMA", "식약처", "허가", "승인", "임상", "3상", "IND", "NDA", "GMP"],
    "CSO/영업": [],
}

CSO_PRIMARY_KEYWORDS = ["CSO", "영업대행", "판매대행", "영업대행사"]
SALES_STRONG_KEYWORDS = [
    "제약영업",
    "의약품 영업",
    "영업조직",
    "영업사원",
    "MR",
    "리베이트",
    "판촉",
    "수수료",
    "거래처",
]
SALES_CONTEXT_KEYWORDS = [
    "처방",
    "병의원",
    "의사",
    "약사",
    "판매",
    "매출",
    "유통",
    "마케팅",
    "프로모션",
    "시장점유율",
    "계약",
    "채널",
]
IMPORTANT_KEYWORDS = [
    "FDA",
    "임상 3상",
    "임상3상",
    "기술수출",
    "허가",
    "급여",
    "보험",
    "약가",
    "M&A",
    "인수",
    "합병",
    "식약처",
    "비만치료제",
    "GLP-1",
    "바이오시밀러",
]
BASE_KEYWORDS = [
    "제약",
    "바이오",
    "신약",
    "임상",
    "FDA",
    "식약처",
    "급여",
    "보험",
    "약가",
    "CSO",
    "비만치료제",
    "항암제",
    "바이오시밀러",
    "기술수출",
    "허가",
]


def is_dailypharm(item: NewsItem) -> bool:
    value = f"{item.title} {item.link} {item.source}".lower()
    return "dailypharm" in value or "데일리팜" in value


def _contains_keyword(text: str, keyword: str) -> bool:
    if keyword in {"CSO", "MR"}:
        return bool(re.search(rf"\b{keyword}\b", text, re.IGNORECASE))
    if keyword in {"약사", "의사"}:
        return bool(re.search(rf"(?<![가-힣]){keyword}(?![가-힣])", text))
    return keyword.upper() in text.upper()


def cso_sales_relevance(item: NewsItem) -> int:
    title = item.title or ""
    text = f"{item.title} {item.summary}"

    if _contains_keyword(title, "CSO"):
        return 100
    if _contains_keyword(text, "CSO"):
        return 80
    if any(_contains_keyword(title, keyword) for keyword in CSO_PRIMARY_KEYWORDS[1:]):
        return 70
    if any(_contains_keyword(text, keyword) for keyword in SALES_STRONG_KEYWORDS):
        return 50

    context_hits = sum(
        1 for keyword in SALES_CONTEXT_KEYWORDS if _contains_keyword(text, keyword)
    )
    if context_hits >= 2:
        return 25 + min(context_hits, 5)
    return 0


def classify(item: NewsItem, dailypharm_bonus: int) -> NewsItem:
    text = f"{item.title} {item.summary}".upper()
    sales_relevance = cso_sales_relevance(item)

    if sales_relevance >= 50:
        item.category = "CSO/영업"
    else:
        item.category = "시장/품목"
        for category in CLASSIFICATION_ORDER:
            if category == "CSO/영업":
                if sales_relevance > 0:
                    item.category = category
                    break
                continue
            keywords = CATEGORY_KEYWORDS[category]
            if any(keyword.upper() in text for keyword in keywords):
                item.category = category
                break

    item.audience = "CSO/제약영업 관점" if sales_relevance > 0 else "제약/바이오 일반"
    item.meta["cso_sales_relevance"] = str(sales_relevance)

    score = 0
    for keyword in IMPORTANT_KEYWORDS:
        if keyword.upper() in text:
            score += 3
    for keyword in BASE_KEYWORDS:
        if keyword.upper() in text:
            score += 1
    if sales_relevance >= 100:
        score += 20
    elif sales_relevance >= 80:
        score += 14
    elif sales_relevance >= 50:
        score += 8
    elif sales_relevance > 0:
        score += 3
    if is_dailypharm(item):
        score += dailypharm_bonus

    item.score = score
    return item
