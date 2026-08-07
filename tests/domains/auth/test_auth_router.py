from httpx import AsyncClient

SIGNUP_PAYLOAD = {
    "id": "layer2026",
    "nickname": "레이어",
    "password": "password1234",
    "passwordConfirm": "password1234",
}


async def test_check_id_with_unused_id_returns_available_true(client: AsyncClient):
    response = await client.get("/api/v1/auth/id/check", params={"id": "layer2026"})

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": {"available": True}}


async def test_check_id_with_taken_id_returns_available_false(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    response = await client.get("/api/v1/auth/id/check", params={"id": "layer2026"})

    assert response.json()["data"]["available"] is False


async def test_signup_with_valid_data_returns_201(client: AsyncClient):
    response = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["userId"]


async def test_signup_with_duplicate_id_returns_duplicate_id_error(
    client: AsyncClient,
):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    response = await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_ID"


async def test_login_with_valid_credentials_returns_tokens(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    response = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accessToken"] and data["refreshToken"]
    assert data["user"]["loginId"] == "layer2026"
    assert data["user"]["nickname"] == "레이어"


async def test_login_first_time_returns_activate_onboarding_true(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    credentials = {"id": "layer2026", "password": "password1234"}

    first = await client.post("/api/v1/auth/login", json=credentials)
    second = await client.post("/api/v1/auth/login", json=credentials)

    assert first.json()["data"]["activateOnboarding"] is True
    assert second.json()["data"]["activateOnboarding"] is False


async def test_login_with_wrong_password_returns_invalid_credentials_error(
    client: AsyncClient,
):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)

    response = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_refresh_with_valid_token_rotates_tokens(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    login = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )
    refresh_token = login.json()["data"]["refreshToken"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["refreshToken"] != refresh_token


async def test_refresh_with_reused_token_returns_refresh_token_reused_error(
    client: AsyncClient,
):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    login = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )
    refresh_token = login.json()["data"]["refreshToken"]
    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": refresh_token}
    )
    new_refresh_token = rotated.json()["data"]["refreshToken"]

    response = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": refresh_token}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"

    # 탈취 탐지 시 전체 세션이 폐기되어 회전된 토큰도 사용할 수 없다.
    retry = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": new_refresh_token}
    )
    assert retry.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"


async def test_logout_revokes_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    login = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )
    refresh_token = login.json()["data"]["refreshToken"]

    response = await client.post(
        "/api/v1/auth/logout", json={"refreshToken": refresh_token}
    )

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": None}

    reuse = await client.post(
        "/api/v1/auth/refresh", json={"refreshToken": refresh_token}
    )
    assert reuse.json()["error"]["code"] == "REFRESH_TOKEN_REUSED"


async def test_request_without_token_returns_token_expired_error(client: AsyncClient):
    response = await client.delete("/api/v1/auth/delete")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


async def test_request_with_invalid_token_returns_token_expired_error(
    client: AsyncClient,
):
    response = await client.delete(
        "/api/v1/auth/delete", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


async def test_delete_account_removes_user(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.delete("/api/v1/auth/delete", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"success": True, "data": None}

    # 계정이 삭제되어 아이디를 다시 사용할 수 있고, 기존 토큰은 통하지 않는다.
    check = await client.get("/api/v1/auth/id/check", params={"id": "layer2026"})
    assert check.json()["data"]["available"] is True

    retry = await client.delete("/api/v1/auth/delete", headers=auth_headers)
    assert retry.json()["error"]["code"] == "TOKEN_EXPIRED"
