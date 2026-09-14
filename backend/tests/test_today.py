from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from tests.conftest import DEVICE


async def test_today_creates_profile_and_returns_shape(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    res = await client.get("/today", headers={"X-Device-Id": DEVICE})
    assert res.status_code == 200
    body = res.json()
    assert body["dayNumber"] == 1
    assert body["reviewDue"] == 0
    assert body["deck"] == {"caught": 0, "mastered": 0, "due": 0, "nextDue": None}
    assert body["nextScene"]["id"] == "cafe"
    assert body["nextScene"]["status"] == "next"
    assert body["nextScene"]["characterName"] == "Léa"

    doc = await mock_client["stumble_test"].profiles.find_one({"device_id": DEVICE})
    assert doc is not None
    assert doc["language"] == "fr"


async def test_profile_is_idempotent(client: AsyncClient) -> None:
    first = await client.post("/profiles", headers={"X-Device-Id": DEVICE})
    second = await client.post("/profiles", headers={"X-Device-Id": DEVICE})
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert set(first.json()) == {"id", "deviceId", "language", "createdAt", "onboarded"}
    assert first.json()["onboarded"] is False


async def test_leaving_the_intro_marks_the_profile_onboarded(client: AsyncClient) -> None:
    before = (await client.get("/today", headers={"X-Device-Id": DEVICE})).json()
    assert before["onboarded"] is False
    res = await client.post("/profiles/onboarded", headers={"X-Device-Id": DEVICE})
    assert res.status_code == 200, res.text
    assert res.json()["onboarded"] is True
    after = (await client.get("/today", headers={"X-Device-Id": DEVICE})).json()
    assert after["onboarded"] is True
