"""Provider interfaces. Real and fake implementations satisfy them; the app sees only these."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Transcript:
    text: str
    duration_s: float | None = None


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class Transcriber(Protocol):
    async def transcribe(
        self, audio: bytes, mime: str, *, language: str, prompt: str | None = None
    ) -> Transcript: ...


class ChatModel(Protocol):
    async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]: ...


class Synthesizer(Protocol):
    content_type: str

    def stream(self, text: str, *, speed: float = 1.0) -> AsyncIterator[bytes]: ...


class ProviderError(Exception):
    """A provider failed. `message` is for the learner's screen: no URLs, no status codes. A
    rate limit is a 503 with `retry_after`, so the client knows it is a moment, not an outage."""

    def __init__(
        self, provider: str, message: str, *, status: int = 502, retry_after: int | None = None
    ) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.message = message
        self.status = status
        self.retry_after = retry_after
