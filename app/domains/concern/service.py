from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.concern.repository import ConcernRepository
from app.domains.concern.schemas import (
    ConcernCreateRequest,
    ConcernCreateResponse,
    ConcernTimelineResponse,
    PastRecordListResponse,
    PastRecordResponse,
    PendingConcernListResponse,
    PendingConcernResponse,
    RecordCreateRequest,
    RecordCreateResponse,
    TimelineRecordResponse,
)


class ConcernService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.concerns = ConcernRepository(session)

    async def create_concern(
        self, user_id: str, payload: ConcernCreateRequest
    ) -> ConcernCreateResponse:
        """새 고민과 첫 기록을 함께 생성한다."""
        concern = await self.concerns.create_concern(
            user_id=user_id,
            concern=payload.concern,
            topic=payload.topic,
            topic_other=payload.topic_other,
            status=payload.concern_status,
        )
        record = await self.concerns.create_record(
            concern_id=concern.id,
            user_id=user_id,
            decision=payload.decision,
            reason=payload.reason,
            value=payload.value,
        )
        await self.session.commit()
        return ConcernCreateResponse(concern_id=concern.id, record_id=record.id)

    async def list_pending_concerns(self, user_id: str) -> PendingConcernListResponse:
        rows = await self.concerns.list_pending_concerns(user_id)
        return PendingConcernListResponse(
            ongoing_concerns=[
                PendingConcernResponse(
                    concern_id=concern.id,
                    concern=concern.concern,
                    topic=concern.topic,
                    topic_other=concern.topic_other,
                    last_record_date=last_record_at.date(),
                    record_count=record_count,
                )
                for concern, last_record_at, record_count in rows
            ]
        )

    async def list_past_records(
        self, user_id: str, concern_id: str
    ) -> PastRecordListResponse | None:
        concern = await self.concerns.get_concern(user_id, concern_id)
        if concern is None:
            return None

        records = await self.concerns.list_records_by_concern(
            concern_id, newest_first=True
        )
        return PastRecordListResponse(
            concern=concern.concern,
            records=[
                PastRecordResponse(
                    record_id=record.id,
                    decision=record.decision,
                    value=record.value,
                    created_at=record.created_at.date(),
                )
                for record in records
            ],
        )

    async def create_record(
        self, user_id: str, concern_id: str, payload: RecordCreateRequest
    ) -> RecordCreateResponse | None:
        concern = await self.concerns.get_concern(user_id, concern_id)
        if concern is None:
            return None

        record = await self.concerns.create_record(
            concern_id=concern.id,
            user_id=user_id,
            decision=payload.decision,
            reason=payload.reason,
            value=payload.value,
        )
        concern.status = payload.concern_status
        await self.session.commit()
        return RecordCreateResponse(record_id=record.id)

    async def get_timeline(
        self, user_id: str, concern_id: str
    ) -> ConcernTimelineResponse | None:
        concern = await self.concerns.get_concern(user_id, concern_id)
        if concern is None:
            return None

        records = await self.concerns.list_records_by_concern(
            concern_id, newest_first=False
        )
        return ConcernTimelineResponse(
            concern=concern.concern,
            topic=concern.topic,
            topic_other=concern.topic_other,
            records=[
                TimelineRecordResponse(
                    record_id=record.id,
                    decision=record.decision,
                    value=record.value,
                    created_at=record.created_at.date(),
                )
                for record in records
            ],
            record_count=len(records),
        )
