from httpx import AsyncClient

from tests.conftest import HEADERS


async def _start(client: AsyncClient, scene: str = "cafe") -> dict:  # type: ignore[type-arg]
    res = await client.post("/sessions", json={"sceneId": scene}, headers=HEADERS)
    assert res.status_code == 200, res.text
    body: dict = res.json()  # type: ignore[type-arg]
    return body


async def test_start_session_has_opening_line_and_audio_url(client: AsyncClient) -> None:
    body = await _start(client)
    assert body["sceneId"] == "cafe"
    assert body["characterName"] == "Léa"
    assert body["done"] is False
    assert body["ttsProvider"] == "browser"
    assert set(body) >= {"id", "turns", "goalProgress", "patience", "sceneColor"}
    opening = body["turns"][0]
    assert opening["role"] == "character"
    assert opening["text"].startswith("Bonjour")
    assert opening["audioUrl"] == f"/sessions/{body['id']}/turns/{opening['id']}/audio"


async def test_unknown_scene_is_404(client: AsyncClient) -> None:
    res = await client.post("/sessions", json={"sceneId": "nope"}, headers=HEADERS)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "scene_not_found"


async def test_unknown_body_field_is_422(client: AsyncClient) -> None:
    res = await client.post("/sessions", json={"sceneId": "cafe", "bogus": 1}, headers=HEADERS)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


async def test_text_turn_catches_code_switch(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.post(
        f"/sessions/{session['id']}/turns",
        data={"text": "Je voudrais un coffee au lait, s'il vous plaît.", "clientPauseMs": "0"},
        headers=HEADERS,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["turns"]) == 3
    learner, reply = body["turns"][1], body["turns"][2]
    assert learner["role"] == "learner"
    assert learner["stumbles"][0]["type"] == "code_switch"
    assert learner["stumbles"][0]["said"] == "coffee"
    assert learner["stumbles"][0]["target"] == "café"
    assert "___" in learner["stumbles"][0]["context"]
    assert reply["role"] == "character"
    assert reply["textEn"]
    assert reply["audioUrl"]
    assert 0 < body["goalProgress"] < 1


async def test_audio_turn_is_transcribed(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.post(
        f"/sessions/{session['id']}/turns",
        files={"audio": ("turn.webm", b"\x00" * 4000, "audio/webm")},
        data={"clientPauseMs": "4200"},
        headers=HEADERS,
    )
    assert res.status_code == 200, res.text
    learner = res.json()["turns"][1]
    assert learner["text"].startswith("Je voudrais")
    assert learner["pauseMs"] == 4200
    # The pause annotation reaches the model, never the card.
    assert "pause_ms" not in learner["stumbles"][0]["context"]


async def test_empty_turn_is_400(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.post(
        f"/sessions/{session['id']}/turns", data={"text": "   "}, headers=HEADERS
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "empty_turn"


async def test_session_finishes_after_goal(client: AsyncClient) -> None:
    session = await _start(client)
    for _ in range(3):
        res = await client.post(
            f"/sessions/{session['id']}/turns", data={"text": "Oui, merci."}, headers=HEADERS
        )
        assert res.status_code == 200
    assert res.json()["done"] is True
    again = await client.post(
        f"/sessions/{session['id']}/turns", data={"text": "Encore."}, headers=HEADERS
    )
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "session_finished"


async def test_turn_audio_streams_without_device_header(client: AsyncClient) -> None:
    session = await _start(client)
    url = session["turns"][0]["audioUrl"]
    first = await client.get(url)
    assert first.status_code == 200
    assert first.headers["content-type"].startswith("audio/")
    assert first.content[:4] == b"RIFF"
    second = await client.get(url)  # served from cache
    assert second.content == first.content


async def test_session_is_owned(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.get(f"/sessions/{session['id']}", headers={"X-Device-Id": "someone-else"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "session_not_found"
