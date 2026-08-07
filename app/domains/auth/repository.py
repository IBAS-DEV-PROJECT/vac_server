from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utc_now
from app.domains.auth.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        if token.revoked_at is None:
            token.revoked_at = utc_now()

    async def revoke_all_by_user(self, user_id: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
