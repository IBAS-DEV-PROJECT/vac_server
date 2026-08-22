from httpx import AsyncClient

BASE_CONCERN = {
    "concern": "A사 vs B사",
    "topic": "일",
    "decision": "아직 못 정함",
    "reason": "조건이 비슷해서",
    "value": "성장",
    "concernStatus": "PENDING",
}


async def create_concern(client: AsyncClient, headers: dict[str, str], **overrides):
    await client.post(
        "/api/v1/concerns", headers=headers, json={**BASE_CONCERN, **overrides}
    )


async def test_get_home_without_records_returns_empty_sections(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get("/api/v1/home", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nickname"] == "레이어"
    assert data["ongoingConcernCount"] == 0
    assert data["ongoingConcerns"] == []
    assert data["recentRecords"] == []
    assert data["monthlyValueHighlight"] is None


async def test_get_home_returns_at_most_three_ongoing_concerns(
    client: AsyncClient, auth_headers: dict[str, str]
):
    for index in range(4):
        await create_concern(client, auth_headers, concern=f"고민 {index}")

    response = await client.get("/api/v1/home", headers=auth_headers)

    data = response.json()["data"]
    assert data["ongoingConcernCount"] == 4
    # 마지막 기록일이 오래된 순으로 최대 3건만 노출한다.
    assert [item["concern"] for item in data["ongoingConcerns"]] == [
        "고민 0",
        "고민 1",
        "고민 2",
    ]


async def test_get_home_returns_recent_records_newest_first(
    client: AsyncClient, auth_headers: dict[str, str]
):
    for index in range(4):
        await create_concern(
            client, auth_headers, concern=f"고민 {index}", decision=f"판단 {index}"
        )

    response = await client.get("/api/v1/home", headers=auth_headers)

    records = response.json()["data"]["recentRecords"]
    assert [record["decision"] for record in records] == ["판단 3", "판단 2", "판단 1"]
    assert records[0]["value"] == "성장"


async def test_get_home_returns_most_selected_value_of_this_month(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="고민 1", value="성장")
    await create_concern(client, auth_headers, concern="고민 2", value="성장")
    await create_concern(client, auth_headers, concern="고민 3", value="안정")

    response = await client.get("/api/v1/home", headers=auth_headers)

    highlight = response.json()["data"]["monthlyValueHighlight"]
    assert highlight["topValue"] == "성장"
    # 직전 월 기록이 없으므로 증감률은 이번 달 비율(67%p)과 같다.
    assert highlight["changeRateVsLastMonth"] == 67


async def test_get_home_excludes_resolved_concerns_from_ongoing(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(
        client, auth_headers, concern="정리됨", concernStatus="RESOLVED"
    )

    response = await client.get("/api/v1/home", headers=auth_headers)

    data = response.json()["data"]
    assert data["ongoingConcernCount"] == 0
    assert data["ongoingConcerns"] == []
    assert len(data["recentRecords"]) == 1


async def test_get_home_returns_topic_other_for_etc_concern(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, topic="기타", topicOther="이사")

    response = await client.get("/api/v1/home", headers=auth_headers)

    concern = response.json()["data"]["ongoingConcerns"][0]
    assert concern["topic"] == "기타"
    assert concern["topicOther"] == "이사"
