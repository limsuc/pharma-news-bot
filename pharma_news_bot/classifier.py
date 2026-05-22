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
    "CSO/영업": ["CSO", "제약영업", "영업", "리베이트", "처방", "병의원", "MR", "마케팅", "대표이사"],
}

CSO_KEYWORDS = ["CSO", "제약영업", "영업", "리베이트", "처방", "병의원", "마케팅", "MR"]
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


def classify(item: NewsItem, dailypharm_bonus: int) -> NewsItem:
    text = f"{item.title} {item.summary}".upper()

    item.category = "시장/품목"
    for category in CLASSIFICATION_ORDER:
        keywords = CATEGORY_KEYWORDS[category]
        if any(keyword.upper() in text for keyword in keywords):
            item.category = category
            break

    item.audience = "CSO/제약영업 관점" if any(keyword.upper() in text for keyword in CSO_KEYWORDS) else "제약/바이오 일반"

    score = 0
    for keyword in IMPORTANT_KEYWORDS:
        if keyword.upper() in text:
            score += 3
    for keyword in BASE_KEYWORDS:
        if keyword.upper() in text:
            score += 1
    if any(keyword.upper() in text for keyword in CSO_KEYWORDS):
        score += 4
    if is_dailypharm(item):
        score += dailypharm_bonus

    item.score = score
    return item
