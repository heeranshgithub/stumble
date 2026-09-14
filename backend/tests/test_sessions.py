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


async def test_stumble_audio_streams_the_target(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.post(
        f"/sessions/{session['id']}/turns",
        data={"text": "Je voudrais un coffee au lait.", "clientPauseMs": "0"},
        headers=HEADERS,
    )
    learner = res.json()["turns"][1]
    stumble = learner["stumbles"][0]
    assert (
        stumble["audioUrl"]
        == f"/sessions/{session['id']}/turns/{learner['id']}/stumbles/0/audio?speed=0.8"
    )
    audio = await client.get(stumble["audioUrl"])
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/")
    missing = await client.get(stumble["audioUrl"].replace("/stumbles/0/", "/stumbles/9/"))
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "stumble_not_found"


def test_mid_scene_replies_do_not_greet_again() -> None:
    from app.services.sessions import _EN_GREETING, _FR_GREETING, _without_regreeting

    assert _without_regreeting("Bonjour ! Un café, très bien. Et avec ça ?", _FR_GREETING) == (
        "Un café, très bien. Et avec ça ?"
    )
    assert _without_regreeting("Hello! A coffee, very good. And with that?", _EN_GREETING) == (
        "A coffee, very good. And with that?"
    )
    # only a greeting: keep it rather than answer with nothing
    assert _without_regreeting("Bonjour !", _FR_GREETING) == "Bonjour !"
    # no greeting: untouched
    assert _without_regreeting("Un café, très bien.", _FR_GREETING) == "Un café, très bien."


async def test_win_audio_streams_the_phrase(client: AsyncClient) -> None:
    session = await _start(client)
    res = await client.post(
        f"/sessions/{session['id']}/turns",
        data={"text": "Je voudrais un coffee au lait, s'il vous plaît.", "clientPauseMs": "0"},
        headers=HEADERS,
    )
    learner = res.json()["turns"][1]
    win = learner["wins"][0]
    assert win["phrase"] == "s'il vous plaît"
    assert win["audioUrl"].startswith(f"/sessions/{session['id']}/wins/")
    audio = await client.get(win["audioUrl"])
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/")
    missing = await client.get(f"/sessions/{session['id']}/wins/nope/audio")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "win_not_found"


def test_a_win_is_credited_only_to_the_turn_that_contains_it() -> None:
    from app.services.sessions import _parse_wins

    raw = [
        {"phrase": "C'est combien"},
        {"phrase": "s'il vous plaît"},
        {"phrase": "Non, c'est tout"},
    ]
    # the model carried the previous turn's wins onto a freeze
    assert _parse_wins(raw, "Euh... je paie...") == []
    # accent- and punctuation-insensitive, so a real one survives
    kept = _parse_wins(raw, "Non, c'est tout. C'est combien ?")
    assert [w["phrase"] for w in kept] == ["C'est combien", "Non, c'est tout"]


def test_a_stumble_below_the_confidence_floor_never_becomes_a_card() -> None:
    from app.services.sessions import _parse_stumbles

    def stumble(target: str, confidence: float) -> dict[str, object]:
        return {
            "type": "miss",
            "said": "Oui",
            "target": target,
            "context": "___.",
            "prompt_line": "C'est tout pour vous ?",
            "confidence": confidence,
        }

    # the model hedged a phantom "miss" on a terse but correct turn
    raw = [stumble("Oui, c'est tout", 0.5), stumble("café au lait", 0.9)]
    assert [s["target"] for s in _parse_stumbles(raw, 0.7)] == ["café au lait"]


def test_the_beat_only_moves_forward_and_the_prompt_names_it() -> None:
    from app.scenes.data import get_scene
    from app.services.prompts import system_prompt
    from app.services.sessions import _next_beat

    assert _next_beat(2, 3, 5) == 3
    # the model drifted back to the order after it was confirmed
    assert _next_beat(2, 1, 5) == 2
    assert _next_beat(2, 9, 5) == 4
    assert _next_beat(2, None, 5) == 2

    cafe = get_scene("cafe")
    assert cafe is not None
    prompt = system_prompt(cafe, "normal", [], beat=2)
    assert "CURRENT BEAT: 2: serve the coffee" in prompt


def test_a_reply_that_trails_off_is_not_a_question() -> None:
    from app.services.sessions import _trails_off

    assert _trails_off("Voilà votre café au lait. Ça vous fera…")
    assert _trails_off("De rien ! Alors...")
    assert not _trails_off("Ça fait 4 euros 50. Vous payez comment ?")
    assert not _trails_off("Voilà votre café au lait.")
