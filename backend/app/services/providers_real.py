"""Groq (speech to text), OpenRouter (chat), ElevenLabs (text to speech). All over httpx."""

import asyncio
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


# A rate limit this short is waited out once, unseen. Longer, and the learner is told to try again.
_RETRY_WAIT_MAX_S = 5


def _retry_after(res: httpx.Response) -> int:
    try:
        return max(1, int(float(res.headers.get("retry-after", "3"))))
    except ValueError:
        return 3


def _error(provider: str, exc: httpx.HTTPError) -> ProviderError:
    """The learner's message. The raw detail (URL, status) goes to the log, not the screen."""
    log.warning("provider_http_error", provider=provider, error=str(exc))
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            return ProviderError(
                provider,
                "Busy for a moment: a few people are speaking at once. Try again in a few seconds.",
                status=503,
                retry_after=_retry_after(exc.response),
            )
        if code in (401, 402, 403):
            return ProviderError(provider, "The voice service isn't available right now.")
        if code >= 500:
            return ProviderError(provider, "The voice service is having trouble. Try again.")
        return ProviderError(provider, "That didn't go through. Try again.")
    if isinstance(exc, httpx.TimeoutException):
        return ProviderError(provider, "That took too long. Try again.")
    return ProviderError(provider, "Couldn't reach the voice service. Try again.")


def _ext(mime: str) -> str:
    base = mime.split(";", 1)[0].strip().lower()
    return _EXT_BY_MIME.get(base, "webm")


# What Whisper says when handed silence and told it is French: the caption credits and outros
# that follow silence in its training data. A transcript that is only one of these is nothing.
_SILENCE_HALLUCINATIONS = {
    "sous-titrage société radio-canada",
    "sous-titrage societe radio-canada",
    "sous-titres réalisés par la communauté d'amara.org",
    "sous-titres réalisés para la communauté d'amara.org",
    "merci d'avoir regardé",
    "merci d'avoir regardé cette vidéo",
    "abonnez-vous",
    "n'hésitez pas à vous abonner",
}


def _heard_nothing(text: str) -> bool:
    t = text.strip().strip(".!… ").casefold()
    return not t or t in _SILENCE_HALLUCINATIONS


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
            res = await self._post(data, audio, mime)
            if res.status_code == 429 and _retry_after(res) <= _RETRY_WAIT_MAX_S:
                log.info("stt_rate_limited", wait_s=_retry_after(res))
                await asyncio.sleep(_retry_after(res))
                res = await self._post(data, audio, mime)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise _error("groq", exc) from exc
        body = res.json()
        text = str(body.get("text", "")).strip()
        if _heard_nothing(text):
            log.info("stt_silence", heard=text)
            text = ""
        return Transcript(text=text, duration_s=body.get("duration"))

    async def _post(self, data: dict[str, str], audio: bytes, mime: str) -> httpx.Response:
        return await self._client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {self._key}"},
            data=data,
            files={"file": (f"turn.{_ext(mime)}", audio, mime.split(";", 1)[0])},
        )


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
                raise _error("openrouter", exc) from exc
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

    async def stream(self, text: str, *, speed: float = 1.0) -> AsyncIterator[bytes]:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice}/stream"
        try:
            async with self._client.stream(
                "POST",
                url,
                params={"output_format": "mp3_44100_64"},
                headers={"xi-api-key": self._key, "accept": "audio/mpeg"},
                json={
                    "text": text,
                    "model_id": self._model,
                    "language_code": "fr",
                    # 0.7 to 1.2 on this model. A phrase to be repeated is slower than a line.
                    "voice_settings": {"speed": max(0.7, min(1.2, speed))},
                },
            ) as res:
                res.raise_for_status()
                async for chunk in res.aiter_bytes():
                    yield chunk
        except httpx.HTTPError as exc:
            raise _error("elevenlabs", exc) from exc
