from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.common.constants import ConcernStatus
from app.common.dependencies import CurrentUser, SessionDep
from app.common.response import SuccessResponse, success
from app.common.utils import parse_multi_query
from app.domains.insight.schemas import InsightResponse, TopicRecordListResponse
from app.domains.insight.service import InsightService

router = APIRouter(prefix="/insights", tags=["insights"])

StartDateQuery = Annotated[date | None, Query(alias="startDate")]
EndDateQuery = Annotated[date | None, Query(alias="endDate")]


@router.get("", response_model=SuccessResponse[InsightResponse])
async def get_insights(
    current_user: CurrentUser,
    session: SessionDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
    topics: Annotated[list[str] | None, Query()] = None,
    values: Annotated[list[str] | None, Query()] = None,
    status: Annotated[ConcernStatus | None, Query()] = None,
) -> dict:
    data = await InsightService(session).get_insights(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        topics=parse_multi_query(topics),
        values=parse_multi_query(values),
        status=status,
    )
    return success(data)


@router.get("/{topic}/records", response_model=SuccessResponse[TopicRecordListResponse])
async def get_topic_records(
    topic: str,
    current_user: CurrentUser,
    session: SessionDep,
    start_date: StartDateQuery = None,
    end_date: EndDateQuery = None,
) -> dict:
    data = await InsightService(session).get_topic_records(
        user_id=current_user.id,
        topic=topic,
        start_date=start_date,
        end_date=end_date,
    )
    return success(data)
