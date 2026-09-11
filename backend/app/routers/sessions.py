from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response

from app.deps import DbDep, ProfileDep, SettingsDep
from app.errors import BadRequest, NotFound
from app.models.card import DebriefDto
from app.models.session import SessionDto, StartSessionRequest
from app.scenes.data import get_scene
from app.services import cards, debrief, sessions, tts
from app.services.registry import Providers

router = APIRouter()

MAX_AUDIO_BYTES = 8 * 1024 * 1024


def _providers(request: Request) -> Providers:
    providers: Providers = request.app.state.providers
    return providers


@router.post("/sessions", response_model=SessionDto)
async def start_session(
    body: StartSessionRequest,
    db: DbDep,
    profile: ProfileDep,
    settings: SettingsDep,
    request: Request,
) -> SessionDto:
    scene = get_scene(body.scene_id)
    if scene is None:
        raise NotFound("Scene not found.", code="scene_not_found")
    # The character is told which words are due, so the scene steers toward them.
    window = timedelta(hours=settings.due_window_hours)
    due = [c["target"] for c in await cards.due_cards(db, profile["_id"], window, limit=5)]
    doc = await sessions.start(db, profile, scene, body.patience, due_cards=due)
    return sessions.to_dto(doc)


@router.get("/sessions/{session_id}", response_model=SessionDto)
async def get_session(
    session_id: str, db: DbDep, profile: ProfileDep, request: Request
) -> SessionDto:
    doc = await sessions.get_owned(db, profile, session_id)
    return sessions.to_dto(doc)


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
    return sessions.to_dto(updated)


@router.post("/sessions/{session_id}/finish", response_model=DebriefDto)
async def finish_session(
    session_id: str, db: DbDep, profile: ProfileDep, settings: SettingsDep
) -> DebriefDto:
    """Ends the scene, reached or not; stumbles become cards; returns the debrief. Idempotent."""
    doc = await sessions.get_owned(db, profile, session_id)
    return await debrief.finish(db, profile, doc, timedelta(hours=settings.due_window_hours))


@router.get("/sessions/{session_id}/turns/{turn_id}/audio")
async def turn_audio(session_id: str, turn_id: str, db: DbDep, request: Request) -> Response:
    """Streams the character's line. Fetched by an <audio> element, so no device header here."""
    doc = await sessions.get_any(db, session_id)
    turn = next((t for t in doc["turns"] if t["id"] == turn_id and t["role"] == "character"), None)
    if turn is None:
        raise NotFound("Turn not found.", code="turn_not_found")
    return await tts.stream_cached(request, f"{session_id}:{turn_id}", turn["text"])


@router.get("/sessions/{session_id}/turns/{turn_id}/stumbles/{index}/audio")
async def stumble_audio(
    session_id: str, turn_id: str, index: int, db: DbDep, request: Request
) -> Response:
    """One stumble's target, spoken. Fetched by an <audio> element, so no device header here."""
    doc = await sessions.get_any(db, session_id)
    turn = next((t for t in doc["turns"] if t["id"] == turn_id and t["role"] == "learner"), None)
    stumbles = turn.get("stumbles", []) if turn else []
    if not 0 <= index < len(stumbles):
        raise NotFound("Stumble not found.", code="stumble_not_found")
    return await tts.stream_cached(
        request, f"{session_id}:{turn_id}:s{index}", stumbles[index]["target"]
    )
