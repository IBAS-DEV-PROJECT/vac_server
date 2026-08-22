from datetime import date

from app.common.response import CamelModel


class ValueDistributionResponse(CamelModel):
    value: str
    percentage: int


class ValueByTopicResponse(CamelModel):
    topic: str
    # 인사이트는 "기타" 주제를 사용자 입력값과 무관하게 하나로 묶어 집계하므로
    # 명세서 호환을 위해 필드만 유지하고 항상 null을 내려준다.
    topic_other: str | None = None
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
    # ValueByTopicResponse.topic_other 와 같은 이유로 항상 null이다.
    topic_other: str | None = None
    records: list[TopicRecordResponse]
    record_count: int
