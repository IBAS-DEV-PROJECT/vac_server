from httpx import AsyncClient

from app.core.config import settings

ALLOWED_ORIGIN = settings.cors_origin_list[0]


async def test_preflight_from_allowed_origin_returns_200(client: AsyncClient):
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


async def test_preflight_from_disallowed_origin_has_no_cors_header(
    client: AsyncClient,
):
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://attacker.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers
