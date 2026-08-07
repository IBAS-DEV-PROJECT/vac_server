from datetime import UTC, datetime

from httpx import AsyncClient

BASE_CONCERN = {
    "concern": "A사 vs B사",
    "topic": "일",
    "decision": "아직 못 정함",
    "reason": "조건이 비슷해서",
    "value": "성장",
    "concernStatus": "PENDING",
}


def today_params() -> dict[str, str]:
    today = datetime.now(UTC).date().isoformat()
    return {"startDate": today, "endDate": today}


async def create_concern(
    client: AsyncClient, headers: dict[str, str], **overrides
) -> str:
    response = await client.post(
        "/api/v1/concerns", headers=headers, json={**BASE_CONCERN, **overrides}
    )
    return response.json()["data"]["concernId"]


async def test_get_insights_without_records_returns_empty_result(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(
        "/api/v1/insights", headers=auth_headers, params=today_params()
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["totalCount"] == 0
    assert data["valueByTopic"] == []
    assert data["largestIncrease"] == []
    assert data["largestDecrease"] == []
    assert data["insight"] == {"mostTopic": [], "mostValue": []}
    # 조회 기간은 항상 4개 구간으로 분할한다.
    assert len(data["trend"]) == 4


async def test_get_insights_returns_value_distribution_by_topic(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="이직", topic="일", value="성장")
    await create_concern(client, auth_headers, concern="승진", topic="일", value="성장")
    await create_concern(
        client, auth_headers, concern="운동", topic="건강", value="안정"
    )

    response = await client.get(
        "/api/v1/insights", headers=auth_headers, params=today_params()
    )

    data = response.json()["data"]
    assert data["totalCount"] == 3
    # 기록 수가 많은 순으로 정렬한다.
    assert [item["topic"] for item in data["valueByTopic"]] == ["일", "건강"]
    assert data["valueByTopic"][0]["count"] == 2
    assert data["valueByTopic"][0]["valueDistribution"] == [
        {"value": "성장", "percentage": 100}
    ]
    assert data["insight"] == {"mostTopic": ["일"], "mostValue": ["성장"]}


async def test_get_insights_with_topic_filter_returns_matching_records_only(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="이직", topic="일", value="성장")
    await create_concern(
        client, auth_headers, concern="운동", topic="건강", value="안정"
    )

    response = await client.get(
        "/api/v1/insights",
        headers=auth_headers,
        params={**today_params(), "topics": "건강"},
    )

    data = response.json()["data"]
    assert data["totalCount"] == 1
    assert [item["topic"] for item in data["valueByTopic"]] == ["건강"]


async def test_get_insights_with_value_filter_returns_matching_records_only(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="이직", topic="일", value="성장")
    await create_concern(
        client, auth_headers, concern="운동", topic="건강", value="안정"
    )

    response = await client.get(
        "/api/v1/insights",
        headers=auth_headers,
        params={**today_params(), "values": "안정"},
    )

    assert response.json()["data"]["totalCount"] == 1


async def test_get_insights_with_single_record_skips_change_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, value="성장")

    response = await client.get(
        "/api/v1/insights", headers=auth_headers, params=today_params()
    )

    data = response.json()["data"]
    assert data["totalCount"] == 1
    assert data["largestIncrease"] == []
    assert data["largestDecrease"] == []


async def test_get_insights_with_tied_values_returns_multiple_most_values(
    client: AsyncClient, auth_headers: dict[str, str]
):
    await create_concern(client, auth_headers, concern="이직", value="성장")
    await create_concern(client, auth_headers, concern="운동", value="안정")

    response = await client.get(
        "/api/v1/insights", headers=auth_headers, params=today_params()
    )

    assert response.json()["data"]["insight"]["mostValue"] == ["성장", "안정"]


async def test_get_topic_records_returns_records_newest_first(
    client: AsyncClient, auth_headers: dict[str, str]
):
    concern_id = await create_concern(
        client, auth_headers, concern="헬스 다시 시작할까", topic="건강", value="안정"
    )
    await client.post(
        f"/api/v1/concerns/pending/{concern_id}",
        headers=auth_headers,
        json={
            "decision": "헬스 다시 시작",
            "reason": "몸이 무거워서",
            "value": "안정",
            "concernStatus": "RESOLVED",
        },
    )
    await create_concern(client, auth_headers, concern="이직", topic="일", value="성장")

    response = await client.get(
        "/api/v1/insights/건강/records", headers=auth_headers, params=today_params()
    )

    data = response.json()["data"]
    assert data["topic"] == "건강"
    assert data["recordCount"] == 2
    assert [record["decision"] for record in data["records"]] == [
        "헬스 다시 시작",
        "아직 못 정함",
    ]
    assert data["records"][0]["concern"] == "헬스 다시 시작할까"
    assert data["records"][0]["concernId"] == concern_id
    assert data["records"][0]["recordDate"]
