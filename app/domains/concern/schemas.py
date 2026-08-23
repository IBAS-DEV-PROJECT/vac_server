from datetime import date
from typing import Self

from pydantic import model_validator

from app.common.constants import ConcernStatus, Topic, Value
from app.common.response import CamelModel


class ConcernCreateRequest(CamelModel):
    concern: str
    topic: Topic
    topic_other: str | None = None
    decision: str
    reason: str
    value: Value
    concern_status: ConcernStatus

    @model_validator(mode="after")
    def check_topic_other(self) -> Self:
        """topic이 기타일 때만 topicOther를 사용하고, 그 외에는 무시한다."""
        if self.topic is not Topic.ETC:
            self.topic_other = None
        elif not (self.topic_other and self.topic_other.strip()):
            raise ValueError("topic이 기타일 때는 topicOther가 필요합니다.")
        else:
            self.topic_other = self.topic_other.strip()
        return self


class ConcernCreateResponse(CamelModel):
    concern_id: str
    record_id: str


class RecordCreateRequest(CamelModel):
    decision: str
    reason: str
    value: Value
    concern_status: ConcernStatus


class RecordCreateResponse(CamelModel):
    record_id: str


class PendingConcernResponse(CamelModel):
    concern_id: str
    concern: str
    topic: str
    topic_other: str | None = None
    last_record_date: date
    record_count: int


class PendingConcernListResponse(CamelModel):
    ongoing_concerns: list[PendingConcernResponse]


class PastRecordResponse(CamelModel):
    record_id: str
    decision: str
    value: str
    created_at: date


class PastRecordListResponse(CamelModel):
    concern: str
    records: list[PastRecordResponse]


class TimelineRecordResponse(CamelModel):
    record_id: str
    decision: str
    value: str
    created_at: date


class ConcernTimelineResponse(CamelModel):
    concern: str
    topic: str
    topic_other: str | None = None
    records: list[TimelineRecordResponse]
    record_count: int
