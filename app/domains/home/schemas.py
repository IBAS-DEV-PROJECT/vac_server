from datetime import date

from app.common.response import CamelModel


class OngoingConcernResponse(CamelModel):
    concern_id: str
    title: str
    topic: str
    last_record_date: date


class MonthlyValueHighlightResponse(CamelModel):
    top_value: str
    change_rate_vs_last_month: int


class RecentRecordResponse(CamelModel):
    record_id: str
    decision: str
    date: date
    value: str


class HomeResponse(CamelModel):
    nickname: str
    ongoing_concern_count: int
    ongoing_concerns: list[OngoingConcernResponse]
    monthly_value_highlight: MonthlyValueHighlightResponse | None
    recent_records: list[RecentRecordResponse]
