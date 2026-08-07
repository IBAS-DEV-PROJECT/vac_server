from fastapi import APIRouter

from app.common.dependencies import CurrentUser, SessionDep
from app.common.response import SuccessResponse, success
from app.domains.home.schemas import HomeResponse
from app.domains.home.service import HomeService

router = APIRouter(prefix="/home", tags=["home"])


@router.get("", response_model=SuccessResponse[HomeResponse])
async def get_home(current_user: CurrentUser, session: SessionDep) -> dict:
    data = await HomeService(session).get_home(current_user)
    return success(data)
