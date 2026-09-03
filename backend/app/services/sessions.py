"""Session lifecycle and the turn pipeline: audio → text → character reply + stumbles → audio."""

import uuid
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError

from app.db import Database, Document
from app.errors import BadRequest, NotFound
from app.log import get_logger
from app.models.session import SessionDto, StumbleDto, TurnDto, WinDto
from app.scenes.data import Scene, get_scene
from app.services.prompts import learner_turn, system_prompt
from app.services.providers import ChatMessage
from app.services.registry import Providers
from app.settings import Settings

log = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _turn(role: str, text: str, goal_progress: float, **extra: Any) -> Document:
    return {
        "id": uuid.uuid4().hex,
        "role": role,
        "text": text,
        "goal_progress": goal_progress,
        "created_at": _now(),
        "stumbles": [],
        "wins": [],
        **extra,
    }


async def start(db: Database, profile: Document, scene: Scene, patience: str) -> Document:
    opening = _turn("character", scene.opening_line, 0.0, text_en=None)
    doc: Document = {
        "profile_id": profile["_id"],
        "scene_id": scene.id,
        "patience": patience,
        "status": "active",
        "goal_progress": 0.0,
        "due_cards": [],
        "turns": [opening],
        "created_at": _now(),
        "finished_at": None,
    }
    result = await db.sessions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def get_owned(db: Database, profile: Document, session_id: str) -> Document:
    try:
        oid = ObjectId(session_id)
    except (InvalidId, TypeError) as exc:
        raise NotFound("Session not found.", code="session_not_found") from exc
    doc: Document | None = await db.sessions.find_one({"_id": oid, "profile_id": profile["_id"]})
    if doc is None:
        raise NotFound("Session not found.", code="session_not_found")
    return doc


async def get_any(db: Database, session_id: str) -> Document:
    """For the audio endpoint, which the browser fetches without headers. Ids are unguessable."""
    try:
        oid = ObjectId(session_id)
    except (InvalidId, TypeError) as exc:
        raise NotFound("Session not found.", code="session_not_found") from exc
    doc: Document | None = await db.sessions.find_one({"_id": oid})
    if doc is None:
        raise NotFound("Session not found.", code="session_not_found")
    return doc


def _messages(session: Document, scene: Scene, settings: Settings) -> list[ChatMessage]:
    msgs = [ChatMessage("system", system_prompt(scene, session["patience"], session["due_cards"]))]
    for t in session["turns"]:
        if t["role"] == "character":
            msgs.append(ChatMessage("assistant", t["text"]))
        else:
            msgs.append(
                ChatMessage(
                    "user",
                    learner_turn(
                        t["text"], int(t.get("pause_ms", 0)), settings.freeze_threshold_ms
                    ),
                )
            )
    return msgs


def _parse_stumbles(raw: Any) -> list[Document]:
    out: list[Document] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            s = StumbleDto.model_validate(item)
        except ValidationError:
            log.warning("stumble_dropped", item=item)
            continue
        if s.target.strip():
            out.append(s.model_dump())
    return out


def _parse_wins(raw: Any) -> list[Document]:
    out: list[Document] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            out.append(WinDto.model_validate(item).model_dump())
        except ValidationError:
            continue
    return out


async def take_turn(
    db: Database,
    providers: Providers,
    settings: Settings,
    session: Document,
    *,
    audio: bytes | None,
    mime: str | None,
    text: str | None,
    pause_ms: int,
) -> Document:
    """Appends the learner's turn and the character's reply; returns the updated session."""
    if session["status"] != "active":
        raise BadRequest("This scene is finished.", code="session_finished")
    scene = get_scene(session["scene_id"])
    if scene is None:  # pragma: no cover - scenes are code
        raise NotFound("Scene not found.", code="scene_not_found")

    if audio:
        transcript = await providers.transcriber.transcribe(
            audio, mime or "audio/webm", language="fr"
        )
        said = transcript.text
    else:
        said = (text or "").strip()
    if not said and pause_ms < settings.freeze_threshold_ms:
        raise BadRequest("Nothing was said.", code="empty_turn")

    learner = _turn("learner", said, session["goal_progress"], pause_ms=pause_ms)
    session["turns"].append(learner)

    result = await providers.chat.complete_json(_messages(session, scene, settings))
    progress = float(result.get("goal_progress", session["goal_progress"]) or 0.0)
    progress = max(session["goal_progress"], min(1.0, progress))
    done = bool(result.get("done", False)) or progress >= 1.0
    learner["stumbles"] = _parse_stumbles(result.get("stumbles"))
    learner["wins"] = _parse_wins(result.get("wins"))
    learner["goal_progress"] = progress

    reply = _turn(
        "character",
        str(result.get("reply", "")).strip() or "Pardon, vous pouvez répéter ?",
        progress,
        text_en=result.get("reply_en"),
    )
    session["turns"].append(reply)
    session["goal_progress"] = progress
    if done:
        session["status"] = "finished"
        session["finished_at"] = _now()

    await db.sessions.update_one(
        {"_id": session["_id"]},
        {
            "$set": {
                "turns": session["turns"],
                "goal_progress": progress,
                "status": session["status"],
                "finished_at": session["finished_at"],
            }
        },
    )
    log.info(
        "turn",
        session_id=str(session["_id"]),
        said=said[:80],
        stumbles=len(learner["stumbles"]),
        progress=progress,
        done=done,
    )
    return session


def to_dto(session: Document, providers: Providers) -> SessionDto:
    scene = get_scene(session["scene_id"])
    if scene is None:  # pragma: no cover
        raise NotFound("Scene not found.", code="scene_not_found")
    sid = str(session["_id"])
    turns = [
        TurnDto(
            id=t["id"],
            role=t["role"],
            text=t["text"],
            text_en=t.get("text_en"),
            stumbles=[StumbleDto.model_validate(s) for s in t.get("stumbles", [])],
            wins=[WinDto.model_validate(w) for w in t.get("wins", [])],
            goal_progress=t["goal_progress"],
            audio_url=f"/sessions/{sid}/turns/{t['id']}/audio"
            if t["role"] == "character"
            else None,
            pause_ms=int(t.get("pause_ms", 0)),
            created_at=t["created_at"],
        )
        for t in session["turns"]
    ]
    return SessionDto(
        _id=session["_id"],
        scene_id=scene.id,
        scene_title=scene.title,
        scene_color=scene.color,
        character_name=scene.character_name,
        character_role=scene.character_role,
        goal=scene.goal,
        patience=session["patience"],
        goal_progress=session["goal_progress"],
        done=session["status"] == "finished",
        tts_provider="browser" if providers.tts_provider == "browser" else "elevenlabs",
        turns=turns,
    )
