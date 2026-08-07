from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.session import get_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """테스트마다 격리된 인메모리 DB를 사용한다."""
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """회원가입 + 로그인을 마친 사용자의 인증 헤더를 반환한다."""
    await client.post(
        "/api/v1/auth/signup",
        json={
            "id": "layer2026",
            "nickname": "레이어",
            "password": "password1234",
            "passwordConfirm": "password1234",
        },
    )
    response = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )
    access_token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {access_token}"}
