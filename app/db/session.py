from collections.abc import AsyncGenerator
from importlib import import_module

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db.base import Base

# Base.metadata에 테이블을 등록하기 위해 반드시 임포트되어야 하는 모델 모듈.
MODEL_MODULES = (
    "app.domains.user.models",
    "app.domains.auth.models",
    "app.domains.concern.models",
)

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """요청 단위 DB 세션 dependency."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """등록된 모델 기준으로 테이블을 생성한다."""
    for module in MODEL_MODULES:
        import_module(module)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
