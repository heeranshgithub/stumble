"""Groq (speech to text), OpenRouter (chat), ElevenLabs (text to speech). All over httpx."""

import json
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.log import get_logger
from app.services.providers import ChatMessage, ProviderError, Transcript

log = get_logger(__name__)

_EXT_BY_MIME = {
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/x-m4a": "m4a",
    "audio/m4a": "m4a",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
}


def _ext(mime: str) -> str:
    base = mime.split(";", 1)[0].strip().lower()
    return _EXT_BY_MIME.get(base, "webm")


class GroqTranscriber:
    def __init__(self, client: httpx.AsyncClient, api_key: str, model: str) -> None:
        self._client = client
        self._key = api_key
        self._model = model

    async def transcribe(
        self, audio: bytes, mime: str, *, language: str, prompt: str | None = None
    ) -> Transcript:
        # `language` alone makes Whisper *translate* English speech into French, turning a
        # code-switch into a clean sentence. The prompt shows it mixed speech, so English stays.
        data = {
            "model": self._model,
            "language": language,
            "response_format": "verbose_json",
            "temperature": "0",
        }
        if prompt:
            data["prompt"] = prompt
        try:
            res = await self._client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._key}"},
                data=data,
                files={"file": (f"turn.{_ext(mime)}", audio, mime.split(";", 1)[0])},
            )
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("groq", str(exc)) from exc
        body = res.json()
        return Transcript(text=str(body.get("text", "")).strip(), duration_s=body.get("duration"))


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class OpenRouterChat:
    def __init__(self, client: httpx.AsyncClient, api_key: str, model: str) -> None:
        self._client = client
        self._key = api_key
        self._model = model

    async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]:
        wire: list[dict[str, str]] = [{"role": m.role, "content": m.content} for m in messages]
        headers = {
            "Authorization": f"Bearer {self._key}",
            "HTTP-Referer": "https://stumble.app",
            "X-Title": "Stumble",
        }
        for attempt in (1, 2):
            payload: dict[str, Any] = {
                "model": self._model,
                "messages": wire,
                "response_format": {"type": "json_object"},
                "temperature": 0.4,
                "max_tokens": 700,
            }
            try:
                res = await self._client.post(
                    "https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers
                )
                res.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError("openrouter", str(exc)) from exc
            content = str(res.json()["choices"][0]["message"]["content"])
            try:
                parsed = json.loads(_FENCE.sub("", content).strip())
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            log.warning("openrouter_bad_json", attempt=attempt, head=content[:120])
            wire = [
                *wire,
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": "That was not valid JSON. Return only the JSON object.",
                },
            ]
        raise ProviderError("openrouter", "model did not return a JSON object")


class ElevenLabsSynthesizer:
    content_type = "audio/mpeg"

    def __init__(self, client: httpx.AsyncClient, api_key: str, voice_id: str, model: str) -> None:
        self._client = client
        self._key = api_key
        self._voice = voice_id
        self._model = model

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice}/stream"
        try:
            async with self._client.stream(
                "POST",
                url,
                params={"output_format": "mp3_44100_64"},
                headers={"xi-api-key": self._key, "accept": "audio/mpeg"},
                json={"text": text, "model_id": self._model, "language_code": "fr"},
            ) as res:
                res.raise_for_status()
                async for chunk in res.aiter_bytes():
                    yield chunk
        except httpx.HTTPError as exc:
            raise ProviderError("elevenlabs", str(exc)) from exc
