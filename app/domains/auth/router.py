from fastapi import APIRouter, Query, status

from app.common.dependencies import CurrentUser, SessionDep
from app.common.response import SuccessResponse, success
from app.domains.auth.schemas import (
    IdCheckResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
)
from app.domains.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/id/check", response_model=SuccessResponse[IdCheckResponse])
async def check_id(session: SessionDep, id: str = Query(...)) -> dict:
    data = await AuthService(session).check_id(id)
    return success(data)


@router.post(
    "/signup",
    response_model=SuccessResponse[SignupResponse],
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest, session: SessionDep) -> dict:
    data = await AuthService(session).signup(
        login_id=payload.id, nickname=payload.nickname, password=payload.password
    )
    return success(data)


@router.post("/login", response_model=SuccessResponse[LoginResponse])
async def login(payload: LoginRequest, session: SessionDep) -> dict:
    data = await AuthService(session).login(
        login_id=payload.id, password=payload.password
    )
    return success(data)


@router.post("/logout", response_model=SuccessResponse[None])
async def logout(payload: RefreshTokenRequest, session: SessionDep) -> dict:
    await AuthService(session).logout(payload.refresh_token)
    return success(None)


@router.delete("/delete", response_model=SuccessResponse[None])
async def delete_account(current_user: CurrentUser, session: SessionDep) -> dict:
    await AuthService(session).delete_account(current_user)
    return success(None)


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(payload: RefreshTokenRequest, session: SessionDep) -> dict:
    data = await AuthService(session).refresh(payload.refresh_token)
    return success(data)
