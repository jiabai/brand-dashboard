from datetime import UTC, datetime, timedelta
from typing import Optional


def get_date_range(
    timeframe: str, specific_date: Optional[str] = None
) -> tuple[datetime.date, datetime.date]:
    """
    根据timeframe参数计算查询的日期范围

    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days', 'specific_day')
        specific_date: 指定日期 (格式: YYYYMMDD)

    Returns:
        tuple: (start_date, end_date)
    """
    if specific_date:
        try:
            end_date = datetime.strptime(specific_date, "%Y%m%d").date()
        except ValueError as exc:
            raise ValueError('日期格式错误，应为YYYYMMDD') from exc
    else:
        end_date = datetime.now(UTC).date()

    if timeframe == "specific_day":
        start_date = end_date
    elif timeframe == "yesterday":
        start_date = end_date - timedelta(days=1)
        end_date = start_date
    elif timeframe == "7days":
        start_date = end_date - timedelta(days=6)
    elif timeframe == "30days":
        start_date = end_date - timedelta(days=29)
    else:
        raise ValueError(f"不支持的时间范围: {timeframe}")

    return start_date, end_date


def get_previous_date_range(timeframe: str, specific_date: Optional[str] = None) -> tuple:
    """
    获取上一周期的时间范围

    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days', 'specific_day')
        specific_date: 指定日期 (格式: YYYYMMDD)

    Returns:
        tuple: (prev_start_date, prev_end_date)
    """
    current_start, current_end = get_date_range(timeframe, specific_date)

    if timeframe == "specific_day":
        prev_start = current_start - timedelta(days=1)
        prev_end = current_end - timedelta(days=1)
    elif timeframe == "yesterday":
        prev_start = current_start - timedelta(days=1)
        prev_end = current_end - timedelta(days=1)
    elif timeframe == "7days":
        days_diff = (current_end - current_start).days + 1
        prev_start = current_start - timedelta(days=days_diff)
        prev_end = current_end - timedelta(days=days_diff)
    elif timeframe == "30days":
        days_diff = (current_end - current_start).days + 1
        prev_start = current_start - timedelta(days=days_diff)
        prev_end = current_end - timedelta(days=days_diff)
    else:
        raise ValueError(f"不支持的时间范围: {timeframe}")

    return prev_start, prev_end