"""Streams synthesized speech for a text, caching the bytes under a key for replays."""

from collections.abc import AsyncIterator

from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.errors import AppError
from app.log import get_logger
from app.services.audio_cache import AudioCache
from app.services.providers import ProviderError
from app.services.registry import Providers

log = get_logger(__name__)

_HEADERS = {"Cache-Control": "private, max-age=86400"}


async def stream_cached(request: Request, key: str, text: str) -> Response:
    """A failure before the first byte is a 502, never an empty 200 mistaken for audio."""
    providers: Providers = request.app.state.providers
    cache: AudioCache = request.app.state.audio_cache
    media_type = providers.synthesizer.content_type

    cached = cache.get(key)
    if cached is not None:
        return Response(content=cached, media_type=media_type, headers=_HEADERS)

    chunks = providers.synthesizer.stream(text)
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
