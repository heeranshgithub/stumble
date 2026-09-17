"""Streams synthesized speech for a text, caching the bytes under a key for replays."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

from app.errors import AppError
from app.log import get_logger
from app.services.audio_cache import AudioCache
from app.services.providers import ProviderError
from app.services.registry import Providers

log = get_logger(__name__)

_HEADERS = {"Cache-Control": "private, max-age=86400"}


# A phrase the learner is about to repeat, not a line in a conversation: slower, cleaner.
PHRASE_SPEED = 0.8


def phrase_url(path: str) -> str:
    """The URL for a phrase's audio. The speed rides in the query string on purpose: audio is
    cached by the browser for a day, so a new pace has to be a new URL or nobody hears it."""
    return f"{path}?speed={PHRASE_SPEED:g}"


def _inflight(app: FastAPI) -> dict[str, asyncio.Task[bytes]]:
    tasks: dict[str, asyncio.Task[bytes]] | None = getattr(app.state, "audio_inflight", None)
    if tasks is None:
        tasks = {}
        app.state.audio_inflight = tasks
    return tasks


async def _synthesize(providers: Providers, text: str, speed: float) -> bytes:
    buf = [chunk async for chunk in providers.synthesizer.stream(text, speed=speed)]
    return b"".join(buf)


def prewarm(app: FastAPI, key: str, text: str, *, speed: float = 1.0) -> None:
    """Starts synthesizing a line into the cache now, so the fetch that follows the reply JSON finds
    it ready and the voice lands with the words. A fetch that arrives mid-synthesis joins it."""
    providers: Providers = app.state.providers
    cache: AudioCache = app.state.audio_cache
    tasks = _inflight(app)
    key = f"{key}@{speed:g}"
    if cache.get(key) is not None or key in tasks:
        return
    task = asyncio.create_task(_synthesize(providers, text, speed))
    tasks[key] = task

    def done(t: asyncio.Task[bytes]) -> None:
        tasks.pop(key, None)
        if t.cancelled():
            return
        if t.exception() is not None:
            log.warning("tts_prewarm_failed", key=key, error=str(t.exception()))
            return
        cache.put(key, t.result())

    task.add_done_callback(done)


async def stream_cached(request: Request, key: str, text: str, *, speed: float = 1.0) -> Response:
    """A failure before the first byte is a 502, never an empty 200 mistaken for audio."""
    providers: Providers = request.app.state.providers
    cache: AudioCache = request.app.state.audio_cache
    media_type = providers.synthesizer.content_type

    key = f"{key}@{speed:g}"
    cached = cache.get(key)
    if cached is not None:
        return Response(content=cached, media_type=media_type, headers=_HEADERS)
    pending = _inflight(request.app).get(key)
    if pending is not None:
        try:
            data = await asyncio.shield(pending)
        except ProviderError as exc:
            raise AppError(
                exc.message,
                code="provider_error",
                status_code=502,
                details={"provider": exc.provider},
            ) from exc
        return Response(content=data, media_type=media_type, headers=_HEADERS)

    chunks = providers.synthesizer.stream(text, speed=speed)
    try:
        first = await anext(chunks)
    except StopAsyncIteration:
        first = b""
    except ProviderError as exc:
        log.warning("tts_unavailable", provider=exc.provider, error=exc.message)
        raise AppError(
            f"{exc.provider} failed: {exc.message}",
            code="provider_error",
            status_code=502,
            details={"provider": exc.provider},
        ) from exc

    async def body() -> AsyncIterator[bytes]:
        buf = [first]
        yield first
        try:
            async for chunk in chunks:
                buf.append(chunk)
                yield chunk
        except ProviderError as exc:
            # Headers are already out; stop, and never cache a fragment as if it were the line.
            log.warning("tts_stream_cut", provider=exc.provider, error=exc.message)
            return
        cache.put(key, b"".join(buf))

    return StreamingResponse(body(), media_type=media_type, headers=_HEADERS)
