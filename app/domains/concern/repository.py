from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import ConcernStatus
from app.domains.concern.models import Concern, Record


class ConcernRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_concern(
        self, user_id: str, concern: str, topic: str, status: str
    ) -> Concern:
        new_concern = Concern(
            user_id=user_id, concern=concern, topic=topic, status=status
        )
        self.session.add(new_concern)
        await self.session.flush()
        return new_concern

    async def create_record(
        self, concern_id: str, user_id: str, decision: str, reason: str, value: str
    ) -> Record:
        record = Record(
            concern_id=concern_id,
            user_id=user_id,
            decision=decision,
            reason=reason,
            value=value,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_concern(self, user_id: str, concern_id: str) -> Concern | None:
        result = await self.session.execute(
            select(Concern).where(Concern.id == concern_id, Concern.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def count_pending_concerns(self, user_id: str) -> int:
        result = await self.session.execute(
            select(func.count(Concern.id)).where(
                Concern.user_id == user_id,
                Concern.status == ConcernStatus.PENDING,
            )
        )
        return result.scalar_one()

    async def list_pending_concerns(
        self, user_id: str, limit: int | None = None
    ) -> list[tuple[Concern, datetime, int]]:
        """진행 중인 고민을 마지막 기록일 오래된 순으로 반환한다.

        각 항목은 (고민, 마지막 기록일, 기록 수) 형태다.
        """
        last_record_at = func.coalesce(
            func.max(Record.created_at), Concern.created_at
        ).label("last_record_at")
        stmt = (
            select(last_record_at, func.count(Record.id).label("record_count"), Concern)
            .outerjoin(Record, Record.concern_id == Concern.id)
            .where(
                Concern.user_id == user_id,
                Concern.status == ConcernStatus.PENDING,
            )
            .group_by(Concern.id)
            .order_by(last_record_at.asc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return [(row.Concern, row.last_record_at, row.record_count) for row in result]

    async def list_records_by_concern(
        self, concern_id: str, *, newest_first: bool = True
    ) -> list[Record]:
        order = Record.created_at.desc() if newest_first else Record.created_at.asc()
        result = await self.session.execute(
            select(Record)
            .where(Record.concern_id == concern_id)
            .order_by(order, Record.id.asc())
        )
        return list(result.scalars().all())

    async def list_records_between(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[Record]:
        """[start, end) 구간에 작성된 기록을 반환한다."""
        result = await self.session.execute(
            select(Record).where(
                Record.user_id == user_id,
                Record.created_at >= start,
                Record.created_at < end,
            )
        )
        return list(result.scalars().all())

    async def list_recent_records(self, user_id: str, limit: int) -> list[Record]:
        result = await self.session.execute(
            select(Record)
            .where(Record.user_id == user_id)
            .order_by(Record.created_at.desc(), Record.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
