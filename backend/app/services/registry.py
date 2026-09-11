"""Builds the provider set from settings. Real needs every key; fake is explicit and loud."""

from dataclasses import dataclass

import httpx

from app.log import get_logger
from app.services.providers import ChatModel, Synthesizer, Transcriber
from app.services.providers_fake import FakeChat, FakeSynthesizer, FakeTranscriber
from app.services.providers_real import ElevenLabsSynthesizer, GroqTranscriber, OpenRouterChat
from app.settings import Settings

log = get_logger(__name__)


@dataclass
class Providers:
    transcriber: Transcriber
    chat: ChatModel
    synthesizer: Synthesizer
    mode: str  # "real" | "fake"
    _client: httpx.AsyncClient | None = None

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()


def build_providers(settings: Settings) -> Providers:
    if settings.providers == "fake":
        log.warning("providers_fake", reason="PROVIDERS=fake: canned replies, no network")
        return Providers(FakeTranscriber(), FakeChat(), FakeSynthesizer(), "fake")

    required = {
        "GROQ_API_KEY": settings.groq_api_key,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "OPENROUTER_MODEL": settings.openrouter_model,
        "ELEVENLABS_API_KEY": settings.elevenlabs_api_key,
        "ELEVENLABS_VOICE_ID": settings.elevenlabs_voice_id,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"PROVIDERS=real but missing: {', '.join(missing)}. "
            "Set them, or PROVIDERS=fake for the explicit offline stand-in."
        )

    client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    return Providers(
        GroqTranscriber(client, settings.groq_api_key or "", settings.groq_stt_model),
        OpenRouterChat(client, settings.openrouter_api_key or "", settings.openrouter_model),
        ElevenLabsSynthesizer(
            client,
            settings.elevenlabs_api_key or "",
            settings.elevenlabs_voice_id or "",
            settings.elevenlabs_model,
        ),
        "real",
        client,
    )
