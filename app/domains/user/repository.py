from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_login_id(self, login_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.login_id == login_id)
        )
        return result.scalar_one_or_none()

    async def exists_login_id(self, login_id: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.login_id == login_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, login_id: str, nickname: str, password_hash: str) -> User:
        user = User(login_id=login_id, nickname=nickname, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
