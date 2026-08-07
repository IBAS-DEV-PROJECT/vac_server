from datetime import UTC, date, datetime, timedelta

TREND_BUCKET_COUNT = 4
DEFAULT_PERIOD_DAYS = 30


def resolve_period(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    """인사이트 조회 기간을 확정한다.

    - 둘 다 없으면 최근 30일
    - 시작일만 있으면 해당 날짜 하루만 조회
    - 종료일만 있으면 종료일 기준 최근 30일
    """
    if start_date is None and end_date is None:
        today = datetime.now(UTC).date()
        return today - timedelta(days=DEFAULT_PERIOD_DAYS - 1), today
    if start_date is not None and end_date is None:
        return start_date, start_date
    if start_date is None and end_date is not None:
        return end_date - timedelta(days=DEFAULT_PERIOD_DAYS - 1), end_date
    return start_date, end_date  # type: ignore[return-value]


def split_buckets(
    start_date: date, end_date: date, count: int = TREND_BUCKET_COUNT
) -> list[tuple[date, date]]:
    """조회 기간을 count개 구간으로 균등 분할한다. 항상 count개를 반환한다."""
    total_days = (end_date - start_date).days + 1
    buckets: list[tuple[date, date]] = []
    for index in range(count):
        bucket_start = start_date + timedelta(days=total_days * index // count)
        bucket_end = start_date + timedelta(
            days=(total_days * (index + 1) // count) - 1
        )
        buckets.append((bucket_start, max(bucket_end, bucket_start)))
    return buckets


def day_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    """날짜 범위를 [시작일 00:00, 종료일 다음날 00:00) UTC 구간으로 변환한다."""
    start = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
    end = datetime.combine(
        end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC
    )
    return start, end


def month_range(target: date) -> tuple[datetime, datetime]:
    """해당 월의 [1일 00:00, 익월 1일 00:00) UTC 구간을 반환한다."""
    first = target.replace(day=1)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    start = datetime.combine(first, datetime.min.time(), tzinfo=UTC)
    end = datetime.combine(next_first, datetime.min.time(), tzinfo=UTC)
    return start, end


def previous_month(target: date) -> date:
    first = target.replace(day=1)
    return first - timedelta(days=1)


def to_percentage(count: int, total: int) -> int:
    if total == 0:
        return 0
    return round(count * 100 / total)


def parse_multi_query(values: list[str] | None) -> list[str] | None:
    """`?topics=A&topics=B` 와 `?topics=A,B` 두 형태를 모두 허용한다."""
    if not values:
        return None
    parsed = [item.strip() for value in values for item in value.split(",")]
    parsed = [item for item in parsed if item]
    return parsed or None
