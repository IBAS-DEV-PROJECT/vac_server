from collections import Counter
from collections.abc import Collection, Sequence
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import day_range, resolve_period, split_buckets, to_percentage
from app.domains.insight.repository import InsightRepository, RecordRow
from app.domains.insight.schemas import (
    InsightResponse,
    InsightSummaryResponse,
    TopicRecordListResponse,
    TopicRecordResponse,
    TrendResponse,
    ValueByTopicResponse,
    ValueDecreaseResponse,
    ValueDistributionResponse,
    ValueIncreaseResponse,
)

MIN_RECORDS_FOR_TREND_ANALYSIS = 2


class InsightService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.insights = InsightRepository(session)

    async def get_insights(
        self,
        user_id: str,
        start_date: date | None,
        end_date: date | None,
        topics: Sequence[str] | None,
        values: Sequence[str] | None,
    ) -> InsightResponse:
        period_start, period_end = resolve_period(start_date, end_date)
        start, end = day_range(period_start, period_end)
        rows = await self.insights.list_records(user_id, start, end, topics, values)

        buckets = split_buckets(period_start, period_end)
        # 조회 기간 전체에 등장한 가치는 모든 구간에 포함하고, 해당 구간에
        # 기록이 없으면 0%로 내려준다.
        period_values = {row.value for row in rows}
        trend = [
            TrendResponse(
                start_date=bucket_start,
                end_date=bucket_end,
                value_distribution=_value_distribution(
                    _rows_in(rows, bucket_start, bucket_end), period_values
                ),
            )
            for bucket_start, bucket_end in buckets
        ]

        increases, decreases = _value_changes(rows, buckets)

        return InsightResponse(
            value_by_topic=_value_by_topic(rows),
            trend=trend,
            largest_increase=increases,
            largest_decrease=decreases,
            insight=InsightSummaryResponse(
                most_topic=_most_common(row.topic for row in rows),
                most_value=_most_common(row.value for row in rows),
            ),
            total_count=len(rows),
        )

    async def get_topic_records(
        self,
        user_id: str,
        topic: str,
        start_date: date | None,
        end_date: date | None,
    ) -> TopicRecordListResponse:
        period_start, period_end = resolve_period(start_date, end_date)
        start, end = day_range(period_start, period_end)
        rows = await self.insights.list_records(user_id, start, end, topics=[topic])

        return TopicRecordListResponse(
            topic=topic,
            records=[
                TopicRecordResponse(
                    record_id=row.record_id,
                    decision=row.decision,
                    value=row.value,
                    concern_id=row.concern_id,
                    concern=row.concern,
                    record_date=row.created_at.date(),
                    concern_status=row.concern_status,
                )
                for row in rows
            ],
            record_count=len(rows),
        )


def _rows_in(
    rows: Sequence[RecordRow], start_date: date, end_date: date
) -> list[RecordRow]:
    return [row for row in rows if start_date <= row.created_at.date() <= end_date]


def _value_distribution(
    rows: Sequence[RecordRow], values: Collection[str] | None = None
) -> list[ValueDistributionResponse]:
    """가치별 비율(%)을 비율 내림차순으로 반환한다.

    values를 넘기면 rows에 없는 가치도 0%로 포함한다.
    """
    total = len(rows)
    counts = Counter(row.value for row in rows)
    for value in values or ():
        counts.setdefault(value, 0)
    return [
        ValueDistributionResponse(value=value, percentage=to_percentage(count, total))
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _value_by_topic(rows: Sequence[RecordRow]) -> list[ValueByTopicResponse]:
    """주제별 가치 분포를 기록 수가 많은 순으로 반환한다."""
    by_topic: dict[str, list[RecordRow]] = {}
    for row in rows:
        by_topic.setdefault(row.topic, []).append(row)

    return [
        ValueByTopicResponse(
            topic=topic,
            value_distribution=_value_distribution(topic_rows),
            count=len(topic_rows),
        )
        for topic, topic_rows in sorted(
            by_topic.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]


def _most_common(items) -> list[str]:
    """최빈값을 반환하며, 동률인 경우 모두 포함한다."""
    counts = Counter(items)
    if not counts:
        return []
    top = max(counts.values())
    return sorted(key for key, count in counts.items() if count == top)


def _value_changes(
    rows: Sequence[RecordRow], buckets: Sequence[tuple[date, date]]
) -> tuple[list[ValueIncreaseResponse], list[ValueDecreaseResponse]]:
    """첫 구간 대비 마지막 구간의 가치 비율 증감(%p)을 계산한다.

    기록이 2건 미만이면 변화 분석을 수행하지 않는다.
    """
    if len(rows) < MIN_RECORDS_FOR_TREND_ANALYSIS:
        return [], []

    first = _distribution_map(_rows_in(rows, *buckets[0]))
    last = _distribution_map(_rows_in(rows, *buckets[-1]))

    deltas = {
        value: last.get(value, 0) - first.get(value, 0)
        for value in set(first) | set(last)
    }
    if not deltas:
        return [], []

    max_delta = max(deltas.values())
    min_delta = min(deltas.values())

    increases = [
        ValueIncreaseResponse(value=value, increase_rate=delta)
        for value, delta in sorted(deltas.items())
        if delta == max_delta and delta > 0
    ]
    decreases = [
        ValueDecreaseResponse(value=value, decrease_rate=delta)
        for value, delta in sorted(deltas.items())
        if delta == min_delta and delta < 0
    ]
    return increases, decreases


def _distribution_map(rows: Sequence[RecordRow]) -> dict[str, int]:
    total = len(rows)
    counts = Counter(row.value for row in rows)
    return {value: to_percentage(count, total) for value, count in counts.items()}
