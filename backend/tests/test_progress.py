from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from tests.conftest import HEADERS


async def _play(client: AsyncClient, *texts: str, scene: str = "cafe") -> str:
    res = await client.post("/sessions", json={"sceneId": scene}, headers=HEADERS)
    sid: str = res.json()["id"]
    for t in texts:
        await client.post(f"/sessions/{sid}/turns", data={"text": t}, headers=HEADERS)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    return sid


async def test_progress_empty(client: AsyncClient) -> None:
    res = await client.get("/progress", headers=HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert body["caught"] == 0
    assert body["scenesCleared"] == 0
    assert len(body["series"]) == 10
    assert body["series"][-1] == {
        "date": datetime.now(UTC).date().isoformat(),
        "caught": 0,
        "mastered": 0,
        "struggling": 0,
    }


async def test_progress_after_scenes(client: AsyncClient) -> None:
    await _play(client, "Un coffee, please.", "Oui.", "Merci.")
    res = await client.get("/progress", headers=HEADERS)
    body = res.json()
    assert body["caught"] == 2
    assert body["scenesCleared"] == 1
    assert body["sessions"] == 1
    assert body["series"][-1]["caught"] == 2
    assert body["series"][-1]["struggling"] == 2
    assert body["series"][0]["caught"] == 0


async def test_deck_states(client: AsyncClient, mock_client: AsyncMongoMockClient) -> None:
    await _play(client, "Un coffee.")
    res = await client.get("/deck", headers=HEADERS)
    body = res.json()
    assert body["caught"] == 1
    card = body["cards"][0]
    assert card["target"] == "café"
    assert card["state"] == "off"
    assert card["sceneTitle"] == "Café"

    await mock_client["stumble_test"].cards.update_many(
        {}, {"$set": {"due": datetime.now(UTC) - timedelta(minutes=1)}}
    )
    assert (await client.get("/deck", headers=HEADERS)).json()["cards"][0]["state"] == "miss"

    await mock_client["stumble_test"].cards.update_many({}, {"$set": {"mastered": True}})
    assert (await client.get("/deck", headers=HEADERS)).json()["cards"][0]["state"] == "on"


async def test_tutor_brief_is_cached_per_week(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _play(client, "Un coffee, please.")
    first = await client.get("/tutor-brief", headers=HEADERS)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["cardsAnalysed"] == 2
    assert body["scenesPlayed"] == 1
    assert len(body["patterns"]) == 2
    assert body["patterns"][0]["title"]
    assert body["suggestedSession"]
    assert "PATTERNS" in body["asText"]
    assert body["weekLabel"].startswith(str(datetime.now(UTC).year))

    second = await client.get("/tutor-brief", headers=HEADERS)
    assert second.json() == body
    assert await mock_client["stumble_test"].briefs.count_documents({}) == 1


async def test_placement_onboards_and_catches_stumbles(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    before = (await client.get("/today", headers=HEADERS)).json()
    assert before["onboarded"] is False

    res = await client.post(
        "/placement", data={"text": "Bonjour, je voudrais un coffee, thanks."}, headers=HEADERS
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["level"] == "A2"
    assert body["cardsAdded"] == 2
    assert {s["target"] for s in body["stumbles"]} == {"café", "merci"}
    assert body["note"]

    after = (await client.get("/today", headers=HEADERS)).json()
    assert after["onboarded"] is True
    assert after["deck"]["caught"] == 2
    profile = await mock_client["stumble_test"].profiles.find_one({})
    assert profile is not None
    assert profile["level"] == "A2"


async def test_placement_empty_is_400(client: AsyncClient) -> None:
    res = await client.post("/placement", data={"text": " "}, headers=HEADERS)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "empty_placement"
