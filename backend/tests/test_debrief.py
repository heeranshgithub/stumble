from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from tests.conftest import DEVICE, HEADERS


async def _start(client: AsyncClient, scene: str = "cafe") -> str:
    res = await client.post("/sessions", json={"sceneId": scene}, headers=HEADERS)
    assert res.status_code == 200
    sid: str = res.json()["id"]
    return sid


async def _say(client: AsyncClient, sid: str, text: str) -> None:
    res = await client.post(f"/sessions/{sid}/turns", data={"text": text}, headers=HEADERS)
    assert res.status_code == 200, res.text


async def test_finish_creates_cards_and_is_idempotent(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    sid = await _start(client)
    await _say(client, sid, "Je voudrais un coffee au lait, please.")
    res = await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    assert res.status_code == 200, res.text
    d = res.json()
    assert d["sessionId"] == sid
    assert d["goalReached"] is False
    assert d["turnsSpoken"] == 1
    assert d["cardsAdded"] == 2
    assert d["cardsRelapsed"] == 0
    assert {s["target"] for s in d["stumbles"]} == {"café", "s'il vous plaît"}
    assert all(s["isNew"] and s["cardId"] for s in d["stumbles"])
    assert d["deck"] == {"caught": 2, "mastered": 0, "due": 0}
    assert d["nextReviewAt"]

    again = await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    assert again.json() == d
    assert await mock_client["stumble_test"].cards.count_documents({}) == 2


async def test_repeat_stumble_is_a_lapse_not_a_new_card(client: AsyncClient) -> None:
    first = await _start(client)
    await _say(client, first, "Un coffee.")
    await client.post(f"/sessions/{first}/finish", headers=HEADERS)

    second = await _start(client)
    await _say(client, second, "Encore un coffee.")
    res = await client.post(f"/sessions/{second}/finish", headers=HEADERS)
    d = res.json()
    assert d["cardsAdded"] == 0
    assert d["cardsRelapsed"] == 1
    assert d["stumbles"][0]["isNew"] is False
    assert d["deck"]["caught"] == 1


async def test_goal_reached_after_three_turns(client: AsyncClient) -> None:
    sid = await _start(client)
    for _ in range(3):
        await _say(client, sid, "Oui, merci.")
    res = await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    assert res.json()["goalReached"] is True
    assert res.json()["turnsSpoken"] == 3


async def test_today_reflects_cards_and_cleared_scene(client: AsyncClient) -> None:
    sid = await _start(client)
    for text in ("Un coffee.", "Oui.", "Merci."):
        await _say(client, sid, text)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)

    res = await client.get("/today", headers={"X-Device-Id": DEVICE})
    body = res.json()
    assert body["deck"]["caught"] == 1
    assert body["nextScene"]["id"] == "pharmacie"


async def test_finish_requires_ownership(client: AsyncClient) -> None:
    sid = await _start(client)
    res = await client.post(f"/sessions/{sid}/finish", headers={"X-Device-Id": "other"})
    assert res.status_code == 404
