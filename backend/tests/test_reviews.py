from datetime import UTC, datetime, timedelta

from bson import ObjectId
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from tests.conftest import HEADERS


async def _make_cards(client: AsyncClient, text: str = "Un coffee, please.") -> str:
    res = await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)
    sid: str = res.json()["id"]
    await client.post(f"/sessions/{sid}/turns", data={"text": text}, headers=HEADERS)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    return sid


async def _make_due(mock_client: AsyncMongoMockClient) -> None:
    """Cards are born due tomorrow; pull them into today for the tests."""
    await mock_client["stumble_test"].cards.update_many(
        {}, {"$set": {"due": datetime.now(UTC) - timedelta(minutes=1)}}
    )


async def test_nothing_due_right_after_a_scene(client: AsyncClient) -> None:
    await _make_cards(client)
    res = await client.get("/reviews/due", headers=HEADERS)
    assert res.status_code == 200
    assert res.json() == {"cards": [], "totalDue": 0}


async def test_due_cards_carry_context_and_intervals(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _make_cards(client)
    await _make_due(mock_client)
    res = await client.get("/reviews/due", headers=HEADERS)
    body = res.json()
    assert body["totalDue"] == 2
    card = body["cards"][0]
    assert set(card) >= {
        "id",
        "sceneTitle",
        "sceneColor",
        "characterName",
        "type",
        "said",
        "target",
        "context",
        "intervals",
        "audioUrl",
    }
    assert set(card["intervals"]) == {"again", "hard", "good", "easy"}
    assert "___" in card["context"]
    assert card["audioUrl"] == f"/reviews/{card['id']}/audio" + "?speed=0.8"


async def test_grade_reschedules_and_counts_down(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _make_cards(client)
    await _make_due(mock_client)
    cards = (await client.get("/reviews/due", headers=HEADERS)).json()["cards"]
    first = cards[0]["id"]

    res = await client.post(f"/reviews/{first}", json={"rating": "good"}, headers=HEADERS)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cardId"] == first
    assert body["rating"] == "good"
    assert body["remainingDue"] == 1
    assert body["interval"].endswith("d")
    assert datetime.fromisoformat(body["due"]) > datetime.now(UTC)

    logs = await mock_client["stumble_test"].reviews.count_documents({})
    assert logs == 1

    today = (await client.get("/today", headers=HEADERS)).json()
    assert today["reviewDue"] == 1
    assert today["sceneUnlocked"] is False


async def test_again_is_a_lapse(client: AsyncClient, mock_client: AsyncMongoMockClient) -> None:
    await _make_cards(client)
    await _make_due(mock_client)
    card = (await client.get("/reviews/due", headers=HEADERS)).json()["cards"][0]
    await client.post(f"/reviews/{card['id']}", json={"rating": "again"}, headers=HEADERS)
    doc = await mock_client["stumble_test"].cards.find_one({"target": card["target"]})
    assert doc is not None
    assert doc["lapses"] == 1


async def test_bad_rating_is_422(client: AsyncClient, mock_client: AsyncMongoMockClient) -> None:
    await _make_cards(client)
    await _make_due(mock_client)
    card = (await client.get("/reviews/due", headers=HEADERS)).json()["cards"][0]
    res = await client.post(f"/reviews/{card['id']}", json={"rating": "meh"}, headers=HEADERS)
    assert res.status_code == 422


async def test_attempt_matches_target(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _make_cards(client, "Un coffee.")
    await _make_due(mock_client)
    card = (await client.get("/reviews/due", headers=HEADERS)).json()["cards"][0]
    assert card["target"] == "café"
    hit = await client.post(
        f"/reviews/{card['id']}/attempt", data={"text": "Un CAFE !"}, headers=HEADERS
    )
    assert hit.json() == {"heard": "Un CAFE !", "matched": True}
    miss = await client.post(
        f"/reviews/{card['id']}/attempt", data={"text": "du thé"}, headers=HEADERS
    )
    assert miss.json()["matched"] is False


async def test_card_audio_streams(client: AsyncClient, mock_client: AsyncMongoMockClient) -> None:
    await _make_cards(client)
    await _make_due(mock_client)
    card = (await client.get("/reviews/due", headers=HEADERS)).json()["cards"][0]
    res = await client.get(card["audioUrl"])
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")


async def test_scenes_track_and_due_words(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    res = await client.get("/scenes", headers=HEADERS)
    statuses = [s["status"] for s in res.json()]
    assert statuses == ["next", "locked", "locked", "locked", "locked", "locked"]

    sid = (await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)).json()["id"]
    for text in ("Un coffee.", "Oui.", "Merci."):
        await client.post(f"/sessions/{sid}/turns", data={"text": text}, headers=HEADERS)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    await _make_due(mock_client)

    res = await client.get("/scenes", headers=HEADERS)
    scenes = res.json()
    assert scenes[0]["status"] == "cleared"
    assert scenes[1]["status"] == "next"
    assert scenes[1]["usesDueCards"] == ["café"]
    # A review is due, so the next scene is next but shut, on the list and at the door.
    assert scenes[1]["unlocked"] is False
    locked = await client.post("/sessions", json={"sceneId": "pharmacie"}, headers=HEADERS)
    assert locked.status_code == 400
    assert locked.json()["error"]["code"] == "scene_locked"

    # A cleared scene replays anytime, and the character is told about the due card.
    started = await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)
    assert started.status_code == 200
    doc = await mock_client["stumble_test"].sessions.find_one(
        {"_id": ObjectId(started.json()["id"])}
    )
    assert doc is not None
    assert doc["due_cards"] == ["café"]


async def _clear_cafe(client: AsyncClient) -> None:
    sid = (await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)).json()["id"]
    for text in ("Un café.", "Oui.", "Merci."):
        await client.post(f"/sessions/{sid}/turns", data={"text": text}, headers=HEADERS)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)


async def test_one_new_scene_per_session(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _clear_cafe(client)
    # Nothing caught, nothing due: the only thing shut is the session gate.
    today = (await client.get("/today", headers=HEADERS)).json()
    assert today["reviewDue"] == 0
    assert today["sceneUnlocked"] is False
    assert today["sceneUnlocksAt"] is not None
    assert today["nextScene"]["id"] == "pharmacie"
    locked = await client.post("/sessions", json={"sceneId": "pharmacie"}, headers=HEADERS)
    assert locked.json()["error"]["code"] == "scene_locked"

    # A session later, it opens.
    await mock_client["stumble_test"].sessions.update_many(
        {}, {"$set": {"finished_at": datetime.now(UTC) - timedelta(hours=9)}}
    )
    today = (await client.get("/today", headers=HEADERS)).json()
    assert today["sceneUnlocked"] is True
    assert today["sceneUnlocksAt"] is None
    started = await client.post("/sessions", json={"sceneId": "pharmacie"}, headers=HEADERS)
    assert started.status_code == 200


async def test_due_now_skips_to_tomorrow(client: AsyncClient) -> None:
    await _clear_cafe(client)
    assert (await client.get("/today", headers=HEADERS)).json()["sceneUnlocked"] is False
    await client.post("/reviews/due-now", headers=HEADERS)
    assert (await client.get("/today", headers=HEADERS)).json()["sceneUnlocked"] is True


async def test_due_now_pulls_tomorrows_cards_into_todays_review(client: AsyncClient) -> None:
    await _make_cards(client)
    before = (await client.get("/reviews/due", headers=HEADERS)).json()
    assert before["totalDue"] == 0  # born today, due tomorrow, by design
    res = await client.post("/reviews/due-now", headers=HEADERS)
    assert res.status_code == 200
    assert res.json()["cards"] >= 1
    after = (await client.get("/reviews/due", headers=HEADERS)).json()
    assert after["totalDue"] == res.json()["cards"]
    # idempotent: nothing left to pull forward
    assert (await client.post("/reviews/due-now", headers=HEADERS)).json()["cards"] == 0
