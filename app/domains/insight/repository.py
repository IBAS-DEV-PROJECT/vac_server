from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.concern.models import Concern, Record


@dataclass(frozen=True, slots=True)
class RecordRow:
    """기록과 소속 고민 정보를 함께 담는 집계용 행."""

    record_id: str
    decision: str
    value: str
    created_at: datetime
    concern_id: str
    concern: str
    topic: str
    concern_status: str


class InsightRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_records(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        topics: Sequence[str] | None = None,
        values: Sequence[str] | None = None,
    ) -> list[RecordRow]:
        """조회 조건에 해당하는 기록을 최신순으로 반환한다."""
        stmt = (
            select(Record, Concern)
            .join(Concern, Concern.id == Record.concern_id)
            .where(
                Record.user_id == user_id,
                Record.created_at >= start,
                Record.created_at < end,
            )
            .order_by(Record.created_at.desc(), Record.id.asc())
        )
        if topics:
            stmt = stmt.where(Concern.topic.in_(list(topics)))
        if values:
            stmt = stmt.where(Record.value.in_(list(values)))

        result = await self.session.execute(stmt)
        return [
            RecordRow(
                record_id=record.id,
                decision=record.decision,
                value=record.value,
                created_at=record.created_at,
                concern_id=concern.id,
                concern=concern.concern,
                topic=concern.topic,
                concern_status=concern.status,
            )
            for record, concern in result
        ]
