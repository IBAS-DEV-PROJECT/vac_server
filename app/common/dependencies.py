from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TokenExpiredException
from app.core.security import decode_access_token
from app.db.session import get_session
from app.domains.user.models import User
from app.domains.user.repository import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(request: Request, session: SessionDep) -> User:
    """`Authorization: Bearer {access_token}` 헤더로 사용자를 식별한다."""
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise TokenExpiredException

    user_id = decode_access_token(token)
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise TokenExpiredException
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
