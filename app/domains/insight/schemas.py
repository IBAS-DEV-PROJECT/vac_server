from datetime import date

from app.common.response import CamelModel


class ValueDistributionResponse(CamelModel):
    value: str
    percentage: int


class ValueByTopicResponse(CamelModel):
    topic: str
    value_distribution: list[ValueDistributionResponse]
    count: int


class TrendResponse(CamelModel):
    start_date: date
    end_date: date
    value_distribution: list[ValueDistributionResponse]


class ValueIncreaseResponse(CamelModel):
    value: str
    increase_rate: int


class ValueDecreaseResponse(CamelModel):
    value: str
    decrease_rate: int


class InsightSummaryResponse(CamelModel):
    most_topic: list[str]
    most_value: list[str]


class InsightResponse(CamelModel):
    value_by_topic: list[ValueByTopicResponse]
    trend: list[TrendResponse]
    largest_increase: list[ValueIncreaseResponse]
    largest_decrease: list[ValueDecreaseResponse]
    insight: InsightSummaryResponse
    total_count: int


class TopicRecordResponse(CamelModel):
    record_id: str
    decision: str
    value: str
    concern_id: str
    concern: str
    record_date: date


class TopicRecordListResponse(CamelModel):
    topic: str
    records: list[TopicRecordResponse]
    record_count: int
