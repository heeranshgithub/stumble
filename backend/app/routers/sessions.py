from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.deps import DbDep, ProfileDep, SettingsDep
from app.errors import AppError, BadRequest, NotFound
from app.models.session import SessionDto, StartSessionRequest
from app.scenes.data import get_scene
from app.services import sessions
from app.services.audio_cache import AudioCache
from app.services.providers import ProviderError
from app.services.registry import Providers

router = APIRouter()

MAX_AUDIO_BYTES = 8 * 1024 * 1024


def _providers(request: Request) -> Providers:
    providers: Providers = request.app.state.providers
    return providers


def _cache(request: Request) -> AudioCache:
    cache: AudioCache = request.app.state.audio_cache
    return cache


@router.post("/sessions", response_model=SessionDto)
async def start_session(
    body: StartSessionRequest, db: DbDep, profile: ProfileDep, request: Request
) -> SessionDto:
    scene = get_scene(body.scene_id)
    if scene is None:
        raise NotFound("Scene not found.", code="scene_not_found")
    doc = await sessions.start(db, profile, scene, body.patience)
    return sessions.to_dto(doc, _providers(request))


@router.get("/sessions/{session_id}", response_model=SessionDto)
async def get_session(
    session_id: str, db: DbDep, profile: ProfileDep, request: Request
) -> SessionDto:
    doc = await sessions.get_owned(db, profile, session_id)
    return sessions.to_dto(doc, _providers(request))


@router.post("/sessions/{session_id}/turns", response_model=SessionDto)
async def take_turn(
    session_id: str,
    db: DbDep,
    profile: ProfileDep,
    settings: SettingsDep,
    request: Request,
    audio: Annotated[UploadFile | None, File()] = None,
    text: Annotated[str | None, Form()] = None,
    client_pause_ms: Annotated[int, Form(alias="clientPauseMs")] = 0,
) -> SessionDto:
    """One learner turn: audio (multipart) or text. Returns the session with the reply appended."""
    doc = await sessions.get_owned(db, profile, session_id)
    audio_bytes: bytes | None = None
    mime: str | None = None
    if audio is not None:
        audio_bytes = await audio.read()
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise BadRequest("Audio is too large.", code="audio_too_large")
        mime = audio.content_type
    try:
        updated = await sessions.take_turn(
            db,
            _providers(request),
            settings,
            doc,
            audio=audio_bytes,
            mime=mime,
            text=text,
            pause_ms=max(0, client_pause_ms),
        )
    except ProviderError as exc:
        raise AppError(
            f"{exc.provider} failed: {exc.message}", code="provider_error", status_code=502
        ) from exc
    return sessions.to_dto(updated, _providers(request))


@router.get("/sessions/{session_id}/turns/{turn_id}/audio")
async def turn_audio(session_id: str, turn_id: str, db: DbDep, request: Request) -> Response:
    """Streams the character's line. Fetched by an <audio> element, so no device header here."""
    doc = await sessions.get_any(db, session_id)
    turn = next((t for t in doc["turns"] if t["id"] == turn_id and t["role"] == "character"), None)
    if turn is None:
        raise NotFound("Turn not found.", code="turn_not_found")

    providers = _providers(request)
    cache = _cache(request)
    key = f"{session_id}:{turn_id}"
    headers = {"Cache-Control": "private, max-age=86400"}

    cached = cache.get(key)
    if cached is not None:
        return Response(
            content=cached, media_type=providers.synthesizer.content_type, headers=headers
        )

    async def body() -> AsyncIterator[bytes]:
        chunks: list[bytes] = []
        try:
            async for chunk in providers.synthesizer.stream(turn["text"]):
                chunks.append(chunk)
                yield chunk
        except ProviderError:
            return
        cache.put(key, b"".join(chunks))

    return StreamingResponse(body(), media_type=providers.synthesizer.content_type, headers=headers)
