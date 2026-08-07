from datetime import date

from app.common.constants import ConcernStatus, Topic, Value
from app.common.response import CamelModel


class ConcernCreateRequest(CamelModel):
    concern: str
    topic: Topic
    decision: str
    reason: str
    value: Value
    concern_status: ConcernStatus


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
    last_record_date: date
    record_count: int


class PendingConcernListResponse(CamelModel):
    ongoing_concerns: list[PendingConcernResponse]


class PastRecordResponse(CamelModel):
    record_id: str
    decision: str
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
    records: list[TimelineRecordResponse]
    record_count: int
