from collections import Counter
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import month_range, previous_month, to_percentage
from app.domains.concern.repository import ConcernRepository
from app.domains.home.schemas import (
    HomeResponse,
    MonthlyValueHighlightResponse,
    OngoingConcernResponse,
    RecentRecordResponse,
)
from app.domains.user.models import User

MAX_ONGOING_CONCERNS = 3
MAX_RECENT_RECORDS = 3


class HomeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.concerns = ConcernRepository(session)

    async def get_home(self, user: User) -> HomeResponse:
        ongoing_count = await self.concerns.count_pending_concerns(user.id)
        ongoing_rows = await self.concerns.list_pending_concerns(
            user.id, limit=MAX_ONGOING_CONCERNS
        )
        recent_records = await self.concerns.list_recent_records(
            user.id, limit=MAX_RECENT_RECORDS
        )

        return HomeResponse(
            nickname=user.nickname,
            ongoing_concern_count=ongoing_count,
            ongoing_concerns=[
                OngoingConcernResponse(
                    concern_id=concern.id,
                    concern=concern.concern,
                    topic=concern.topic,
                    last_record_date=last_record_at.date(),
                )
                for concern, last_record_at, _ in ongoing_rows
            ],
            monthly_value_highlight=await self._monthly_value_highlight(user.id),
            recent_records=[
                RecentRecordResponse(
                    record_id=record.id,
                    decision=record.decision,
                    date=record.created_at.date(),
                    value=record.value,
                )
                for record in recent_records
            ],
        )

    async def _monthly_value_highlight(
        self, user_id: str
    ) -> MonthlyValueHighlightResponse | None:
        """이번 달 대표 가치와, 직전 월 대비 선택 비율의 증감(%p)을 계산한다."""
        today = datetime.now(UTC).date()

        this_start, this_end = month_range(today)
        this_month = await self.concerns.list_records_between(
            user_id, this_start, this_end
        )
        if not this_month:
            return None

        counts = Counter(record.value for record in this_month)
        top_value, top_count = counts.most_common(1)[0]
        this_rate = to_percentage(top_count, len(this_month))

        last_start, last_end = month_range(previous_month(today))
        last_month = await self.concerns.list_records_between(
            user_id, last_start, last_end
        )
        last_rate = to_percentage(
            sum(1 for record in last_month if record.value == top_value),
            len(last_month),
        )

        return MonthlyValueHighlightResponse(
            top_value=top_value,
            change_rate_vs_last_month=this_rate - last_rate,
        )
