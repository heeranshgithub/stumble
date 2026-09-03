"""Streams synthesized speech for a text, caching the bytes under a key for replays."""

from collections.abc import AsyncIterator

from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.services.audio_cache import AudioCache
from app.services.providers import ProviderError
from app.services.registry import Providers

_HEADERS = {"Cache-Control": "private, max-age=86400"}


def stream_cached(request: Request, key: str, text: str) -> Response:
    providers: Providers = request.app.state.providers
    cache: AudioCache = request.app.state.audio_cache
    media_type = providers.synthesizer.content_type

    cached = cache.get(key)
    if cached is not None:
        return Response(content=cached, media_type=media_type, headers=_HEADERS)

    async def body() -> AsyncIterator[bytes]:
        chunks: list[bytes] = []
        try:
            async for chunk in providers.synthesizer.stream(text):
                chunks.append(chunk)
                yield chunk
        except ProviderError:
            return
        cache.put(key, b"".join(chunks))

    return StreamingResponse(body(), media_type=media_type, headers=_HEADERS)
