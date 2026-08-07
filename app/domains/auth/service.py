from datetime import UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateIdException,
    InvalidCredentialsException,
    RefreshTokenReusedException,
    TokenExpiredException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_password,
)
from app.db.base import utc_now
from app.domains.auth.repository import RefreshTokenRepository
from app.domains.auth.schemas import (
    IdCheckResponse,
    LoginResponse,
    LoginUserResponse,
    SignupResponse,
    TokenResponse,
)
from app.domains.user.models import User
from app.domains.user.repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tokens = RefreshTokenRepository(session)

    async def check_id(self, login_id: str) -> IdCheckResponse:
        exists = await self.users.exists_login_id(login_id)
        return IdCheckResponse(available=not exists)

    async def signup(
        self, login_id: str, nickname: str, password: str
    ) -> SignupResponse:
        if await self.users.exists_login_id(login_id):
            raise DuplicateIdException

        user = await self.users.create(
            login_id=login_id,
            nickname=nickname,
            password_hash=hash_password(password),
        )
        await self.session.commit()
        return SignupResponse(user_id=user.id)

    async def login(self, login_id: str, password: str) -> LoginResponse:
        user = await self.users.get_by_login_id(login_id)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsException

        # 첫 로그인에 한해 온보딩을 활성화한다.
        activate_onboarding = not user.onboarding_completed
        if activate_onboarding:
            user.onboarding_completed = True

        access_token, refresh_token = await self._issue_tokens(user.id)
        await self.session.commit()

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=LoginUserResponse(
                id=user.id, login_id=user.login_id, nickname=user.nickname
            ),
            activate_onboarding=activate_onboarding,
        )

    async def logout(self, refresh_token: str) -> None:
        stored = await self.tokens.get_by_hash(hash_refresh_token(refresh_token))
        if stored is not None:
            await self.tokens.revoke(stored)
        await self.session.commit()

    async def refresh(self, refresh_token: str) -> TokenResponse:
        stored = await self.tokens.get_by_hash(hash_refresh_token(refresh_token))
        if stored is None:
            raise TokenExpiredException

        # 이미 폐기된 토큰의 재사용은 탈취로 간주하고 전체 세션을 폐기한다.
        if stored.revoked_at is not None:
            await self.tokens.revoke_all_by_user(stored.user_id)
            await self.session.commit()
            raise RefreshTokenReusedException

        if stored.expires_at.replace(tzinfo=UTC) <= utc_now():
            await self.tokens.revoke(stored)
            await self.session.commit()
            raise TokenExpiredException

        await self.tokens.revoke(stored)
        access_token, new_refresh_token = await self._issue_tokens(stored.user_id)
        await self.session.commit()

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    async def delete_account(self, user: User) -> None:
        await self.tokens.revoke_all_by_user(user.id)
        await self.users.delete(user)
        await self.session.commit()

    async def _issue_tokens(self, user_id: str) -> tuple[str, str]:
        refresh_token = create_refresh_token()
        await self.tokens.create(
            user_id=user_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_token_expires_at(),
        )
        return create_access_token(user_id), refresh_token
