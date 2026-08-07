from fastapi import APIRouter, status

from app.common.dependencies import CurrentUser, SessionDep
from app.common.response import SuccessResponse, success
from app.domains.concern.schemas import (
    ConcernCreateRequest,
    ConcernCreateResponse,
    ConcernTimelineResponse,
    PastRecordListResponse,
    PendingConcernListResponse,
    RecordCreateRequest,
    RecordCreateResponse,
)
from app.domains.concern.service import ConcernService

router = APIRouter(prefix="/concerns", tags=["concerns"])


@router.post(
    "",
    response_model=SuccessResponse[ConcernCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_concern(
    payload: ConcernCreateRequest, current_user: CurrentUser, session: SessionDep
) -> dict:
    data = await ConcernService(session).create_concern(current_user.id, payload)
    return success(data)


@router.get("/pending", response_model=SuccessResponse[PendingConcernListResponse])
async def list_pending_concerns(current_user: CurrentUser, session: SessionDep) -> dict:
    data = await ConcernService(session).list_pending_concerns(current_user.id)
    return success(data)


@router.get(
    "/pending/{concern_id}", response_model=SuccessResponse[PastRecordListResponse]
)
async def list_past_records(
    concern_id: str, current_user: CurrentUser, session: SessionDep
) -> dict:
    data = await ConcernService(session).list_past_records(current_user.id, concern_id)
    return success(data)


@router.post(
    "/pending/{concern_id}",
    response_model=SuccessResponse[RecordCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_record(
    concern_id: str,
    payload: RecordCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    data = await ConcernService(session).create_record(
        current_user.id, concern_id, payload
    )
    return success(data)


@router.get(
    "/{concern_id}/timeline", response_model=SuccessResponse[ConcernTimelineResponse]
)
async def get_timeline(
    concern_id: str, current_user: CurrentUser, session: SessionDep
) -> dict:
    data = await ConcernService(session).get_timeline(current_user.id, concern_id)
    return success(data)
