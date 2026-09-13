"""A provider that fails is a visible 502, never a canned reply or an empty audio body."""

from collections.abc import AsyncIterator
from typing import Any

from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import create_app
from app.services.providers import ChatMessage, ProviderError
from app.services.providers_fake import FakeChat, FakeSynthesizer, FakeTranscriber
from app.services.registry import Providers
from app.settings import Settings
from tests.conftest import HEADERS


class DeadSynthesizer:
    content_type = "audio/mpeg"

    async def stream(self, text: str, *, speed: float = 1.0) -> AsyncIterator[bytes]:
        raise ProviderError("elevenlabs", "quota exceeded")
        yield b""  # pragma: no cover - makes this an async generator


class DeadChat:
    async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]:
        raise ProviderError("openrouter", "402 payment required")


def _client(settings: Settings, providers: Providers) -> AsyncClient:
    app = create_app(settings=settings, db_client=AsyncMongoMockClient(), providers=providers)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_ready_reports_the_provider_mode(client: AsyncClient) -> None:
    res = await client.get("/ready")
    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "providers": "fake",
        "stt": "fake",
        "llm": "fake",
        "tts": "fake",
    }


async def test_dead_tts_is_a_502_not_an_empty_200(settings: Settings) -> None:
    providers = Providers(FakeTranscriber(), FakeChat(), DeadSynthesizer(), "real")
    async with _client(settings, providers) as client:
        session = (await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)).json()
        res = await client.get(session["turns"][0]["audioUrl"])
    assert res.status_code == 502
    body = res.json()["error"]
    assert body["code"] == "provider_error"
    assert body["details"]["provider"] == "elevenlabs"


async def test_dead_llm_is_a_502_with_the_provider_named(settings: Settings) -> None:
    providers = Providers(FakeTranscriber(), DeadChat(), FakeSynthesizer(), "real")
    async with _client(settings, providers) as client:
        session = (await client.post("/sessions", json={"sceneId": "cafe"}, headers=HEADERS)).json()
        res = await client.post(
            f"/sessions/{session['id']}/turns",
            data={"text": "Bonjour", "clientPauseMs": "0"},
            headers=HEADERS,
        )
    assert res.status_code == 502
    assert res.json()["error"]["details"]["provider"] == "openrouter"


def test_whisper_silence_credits_count_as_nothing() -> None:
    from app.services.providers_real import _heard_nothing

    assert _heard_nothing("Sous-titrage Société Radio-Canada")
    assert _heard_nothing(" ... ")
    assert _heard_nothing("Merci d'avoir regardé.")
    assert not _heard_nothing("Merci.")
    assert not _heard_nothing("Je voudrais un café.")
