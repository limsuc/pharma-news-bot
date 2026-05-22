from datetime import datetime, timedelta, timezone

import holidays


KST = timezone(timedelta(hours=9))


def today_kst_date():
    return datetime.now(KST).date()


def is_korea_public_holiday(date=None) -> tuple[bool, str | None]:
    target = date or today_kst_date()
    korea_holidays = holidays.country_holidays("KR", years=[target.year])
    holiday_name = korea_holidays.get(target)
    return holiday_name is not None, holiday_name
