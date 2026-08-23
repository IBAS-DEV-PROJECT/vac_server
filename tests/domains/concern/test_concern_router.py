from httpx import AsyncClient

NEW_CONCERN = {
    "concern": "A사 vs B사",
    "topic": "일",
    "decision": "아직 못 정함",
    "reason": "조건이 비슷해서",
    "value": "성장",
    "concernStatus": "PENDING",
}


async def create_concern(
    client: AsyncClient, headers: dict[str, str], **overrides
) -> str:
    payload = {**NEW_CONCERN, **overrides}
    response = await client.post("/api/v1/concerns", headers=headers, json=payload)
    return response.json()["data"]["concernId"]


async def test_create_concern_with_valid_data_returns_201(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.post(
        "/api/v1/concerns", headers=auth_headers, json=NEW_CONCERN
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["concernId"] and data["recordId"]


async def test_list_pending_concerns_excludes_resolved_concerns(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="진행 중인 고민")
    await create_concern(
        client, auth_headers, concern="정리된 고민", concernStatus="RESOLVED"
    )

    response = await client.get("/api/v1/concerns/pending", headers=auth_headers)

    concerns = response.json()["data"]["ongoingConcerns"]
    assert [concern["concern"] for concern in concerns] == ["진행 중인 고민"]
    assert concerns[0]["recordCount"] == 1
    assert concerns[0]["topic"] == "일"
    assert concerns[0]["lastRecordDate"]


async def test_list_past_records_returns_records_newest_first(
    client: AsyncClient, auth_headers: dict[str, str]
):
    concern_id = await create_concern(client, auth_headers)
    await client.post(
        f"/api/v1/concerns/pending/{concern_id}",
        headers=auth_headers,
        json={
            "decision": "B사로 기움",
            "reason": "안정적이라서",
            "value": "안정",
            "concernStatus": "PENDING",
        },
    )

    response = await client.get(
        f"/api/v1/concerns/pending/{concern_id}", headers=auth_headers
    )

    data = response.json()["data"]
    assert data["concern"] == "A사 vs B사"
    assert [record["decision"] for record in data["records"]] == [
        "B사로 기움",
        "아직 못 정함",
    ]
    assert [record["value"] for record in data["records"]] == ["안정", "성장"]


async def test_create_record_with_resolved_status_removes_concern_from_pending(
    client: AsyncClient, auth_headers: dict[str, str]
):
    concern_id = await create_concern(client, auth_headers)

    response = await client.post(
        f"/api/v1/concerns/pending/{concern_id}",
        headers=auth_headers,
        json={
            "decision": "A사로 결정",
            "reason": "성장 기회가 커서",
            "value": "성장",
            "concernStatus": "RESOLVED",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["recordId"]

    pending = await client.get("/api/v1/concerns/pending", headers=auth_headers)
    assert pending.json()["data"]["ongoingConcerns"] == []


async def test_delete_account_removes_concern_records(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers)

    await client.delete("/api/v1/auth/delete", headers=auth_headers)

    # 동일한 아이디로 재가입해도 이전 고민/기록은 남아 있지 않다.
    await client.post(
        "/api/v1/auth/signup",
        json={
            "id": "layer2026",
            "nickname": "레이어",
            "password": "password1234",
            "passwordConfirm": "password1234",
        },
    )
    login = await client.post(
        "/api/v1/auth/login", json={"id": "layer2026", "password": "password1234"}
    )
    headers = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}

    pending = await client.get("/api/v1/concerns/pending", headers=headers)
    assert pending.json()["data"]["ongoingConcerns"] == []


async def test_get_timeline_returns_records_oldest_first(
    client: AsyncClient, auth_headers: dict[str, str]
):
    concern_id = await create_concern(client, auth_headers)
    await client.post(
        f"/api/v1/concerns/pending/{concern_id}",
        headers=auth_headers,
        json={
            "decision": "A사로 결정",
            "reason": "성장 기회가 커서",
            "value": "성장",
            "concernStatus": "RESOLVED",
        },
    )

    response = await client.get(
        f"/api/v1/concerns/{concern_id}/timeline", headers=auth_headers
    )

    data = response.json()["data"]
    assert data["concern"] == "A사 vs B사"
    assert data["topic"] == "일"
    assert data["recordCount"] == 2
    assert [record["decision"] for record in data["records"]] == [
        "아직 못 정함",
        "A사로 결정",
    ]


async def test_create_concern_with_etc_topic_stores_topic_other(
    client: AsyncClient, auth_headers: dict[str, str]
):
    concern_id = await create_concern(
        client, auth_headers, topic="기타", topicOther="이사"
    )

    pending = await client.get("/api/v1/concerns/pending", headers=auth_headers)
    concern = pending.json()["data"]["ongoingConcerns"][0]
    assert concern["topic"] == "기타"
    assert concern["topicOther"] == "이사"

    timeline = await client.get(
        f"/api/v1/concerns/{concern_id}/timeline", headers=auth_headers
    )
    assert timeline.json()["data"]["topicOther"] == "이사"


async def test_create_concern_with_etc_topic_without_topic_other_returns_422(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.post(
        "/api/v1/concerns",
        headers=auth_headers,
        json={**NEW_CONCERN, "topic": "기타"},
    )

    assert response.status_code == 422


async def test_create_concern_with_normal_topic_ignores_topic_other(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, topic="일", topicOther="이사")

    pending = await client.get("/api/v1/concerns/pending", headers=auth_headers)
    concern = pending.json()["data"]["ongoingConcerns"][0]
    assert concern["topic"] == "일"
    assert concern["topicOther"] is None
