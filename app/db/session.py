from collections.abc import AsyncGenerator
from importlib import import_module
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base

# Base.metadata에 테이블을 등록하기 위해 반드시 임포트되어야 하는 모델 모듈.
MODEL_MODULES = (
    "app.domains.user.models",
    "app.domains.auth.models",
    "app.domains.concern.models",
)


def _engine_kwargs() -> dict[str, Any]:
    """실행 환경에 맞는 엔진 옵션을 만든다.

    Lambda는 실행 환경이 freeze/thaw 되면서 풀에 남은 커넥션이 끊기고, 동시 실행
    수만큼 커넥션이 늘어난다. 따라서 풀링은 RDS Proxy에 맡기고 애플리케이션은
    NullPool 을 사용한다.
    """
    kwargs: dict[str, Any] = {"echo": settings.debug}
    if settings.is_lambda:
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {
            # RDS Proxy 경유 시 서버 사이드 prepared statement 재사용이 불가능하다.
            "statement_cache_size": 0,
            "ssl": settings.db_ssl_mode,
        }
    return kwargs


engine = create_async_engine(settings.resolved_database_url(), **_engine_kwargs())

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """요청 단위 DB 세션 dependency."""
    async with AsyncSessionLocal() as session:
        yield session


def import_models() -> None:
    """Base.metadata 에 모든 테이블이 등록되도록 모델 모듈을 임포트한다."""
    for module in MODEL_MODULES:
        import_module(module)


async def init_db() -> None:
    """등록된 모델 기준으로 테이블을 생성한다 (로컬/테스트 전용)."""
    import_models()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
