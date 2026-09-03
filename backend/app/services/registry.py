"""Builds the provider set from settings. Missing keys fall back to fakes with a loud log line."""

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
    tts_provider: str  # "elevenlabs" | "browser": what the client should use for playback
    mode: str  # "real" | "fake" | "mixed"
    _client: httpx.AsyncClient | None = None

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()


def build_providers(settings: Settings) -> Providers:
    if settings.providers == "fake":
        log.warning("providers_fake", reason="PROVIDERS=fake")
        return Providers(FakeTranscriber(), FakeChat(), FakeSynthesizer(), "browser", "fake")

    client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
    fake: list[str] = []

    transcriber: Transcriber
    if settings.groq_api_key:
        transcriber = GroqTranscriber(client, settings.groq_api_key, settings.groq_stt_model)
    else:
        transcriber = FakeTranscriber()
        fake.append("groq")

    chat: ChatModel
    if settings.openrouter_api_key:
        if not settings.openrouter_model:
            raise RuntimeError("OPENROUTER_API_KEY is set but OPENROUTER_MODEL is empty")
        chat = OpenRouterChat(client, settings.openrouter_api_key, settings.openrouter_model)
    else:
        chat = FakeChat()
        fake.append("openrouter")

    synthesizer: Synthesizer
    tts_provider = settings.tts_provider
    has_voice = bool(settings.elevenlabs_api_key and settings.elevenlabs_voice_id)
    if has_voice and tts_provider == "elevenlabs":
        synthesizer = ElevenLabsSynthesizer(
            client,
            settings.elevenlabs_api_key or "",
            settings.elevenlabs_voice_id or "",
            settings.elevenlabs_model,
        )
    else:
        synthesizer = FakeSynthesizer()
        if not has_voice:
            fake.append("elevenlabs")
        # No real voice: the client speaks with the browser's own synthesizer.
        tts_provider = "browser"

    if settings.providers == "real" and fake:
        raise RuntimeError(f"PROVIDERS=real but keys are missing for: {', '.join(fake)}")

    mode = "real" if not fake else ("fake" if len(fake) == 3 else "mixed")
    if fake:
        log.warning("providers_partial", fake=fake, mode=mode)
    return Providers(transcriber, chat, synthesizer, tts_provider, mode, client)
