"""Session lifecycle and the turn pipeline: audio → text → character reply + stumbles → audio."""

import re
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import ValidationError

from app.db import Database, Document
from app.errors import BadRequest, NotFound
from app.log import get_logger
from app.models.session import SessionDto, StumbleDto, TurnDto, WinDto
from app.scenes.data import Scene, get_scene
from app.services import tts
from app.services.cards import target_key
from app.services.prompts import learner_turn, stt_prompt, system_prompt
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


async def start(
    db: Database,
    profile: Document,
    scene: Scene,
    patience: str,
    due_cards: list[str] | None = None,
) -> Document:
    opening = _turn("character", scene.opening_line, 0.0, text_en=scene.opening_line_en)
    doc: Document = {
        "profile_id": profile["_id"],
        "scene_id": scene.id,
        "patience": patience,
        "status": "active",
        "goal_progress": 0.0,
        "beat": 0,
        "due_cards": due_cards or [],
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


# The character greets once, in the opening line. The prompt says so, and the model still mirrors a
# learner's "Bonjour !" about one turn in six, so the greeting is also dropped here.
_FR_GREETING = re.compile(r"^(bonjour|bonsoir|salut|rebonjour)\s*[!.,]?\s*", re.IGNORECASE)
_EN_GREETING = re.compile(
    r"^(hello|hi|hey|good (morning|afternoon|evening))\s*[!.,]?\s*", re.IGNORECASE
)


def _without_regreeting(text: str, greeting: re.Pattern[str]) -> str:
    """Strips a leading greeting from a mid-scene reply; a reply that is only a greeting is kept."""
    text = text.strip()
    rest = greeting.sub("", text, count=1)
    if not rest or rest == text:
        return text
    return rest[0].upper() + rest[1:]


# A reply that stops mid-sentence ("Ça vous fera…") is the model leaving a blank for the learner
# to fill. One more try, told so; this fires rarely and costs a second when it does.
_TRAILS_OFF = re.compile(r"(\.\.\.|…)\s*$")
_NUDGE = (
    "[Your line stopped mid-sentence. Say the whole thing, with the number or the fact, "
    "then your question. Same JSON.]"
)


def _trails_off(reply: str) -> bool:
    return bool(_TRAILS_OFF.search(reply.strip())) and not reply.strip().endswith("?")


async def _complete(providers: Providers, msgs: list[ChatMessage]) -> dict[str, Any]:
    result = await providers.chat.complete_json(msgs)
    reply = str(result.get("reply", ""))
    if not _trails_off(reply):
        return result
    log.info("reply_trailed_off", reply=reply[:80])
    retry = [*msgs, ChatMessage("assistant", reply), ChatMessage("user", _NUDGE)]
    second = await providers.chat.complete_json(retry)
    return second if str(second.get("reply", "")).strip() else result


def _learner_turns(session: Document) -> int:
    return sum(1 for t in session["turns"] if t["role"] == "learner")


def _messages(session: Document, scene: Scene, settings: Settings) -> list[ChatMessage]:
    msgs = [
        ChatMessage(
            "system",
            system_prompt(
                scene,
                session["patience"],
                session["due_cards"],
                session.get("beat", 0),
                last_turn=_learner_turns(session) >= settings.scene_max_turns,
            ),
        )
    ]
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


def _next_beat(current: int, raw: Any, count: int) -> int:
    """The beat only ever moves forward; the model sometimes drifts back to one already played."""
    try:
        wanted = int(raw)
    except (TypeError, ValueError):
        wanted = current
    return max(current, min(count - 1, wanted))


def _clean_context(context: str) -> str:
    """A card's context is the learner's sentence only, never the pause metadata for the model."""
    return context.split("\n\n[", 1)[0].strip()


# A card is a word or a short phrase. A target longer than this is the model correcting the whole
# sentence, and a five-word cloze is not a review anyone can pass.
_MAX_TARGET_WORDS = 4


def _parse_stumbles(raw: Any, confidence_min: float) -> list[Document]:
    out: list[Document] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            s = StumbleDto.model_validate(item)
        except ValidationError:
            log.warning("stumble_dropped", item=item)
            continue
        if not s.target.strip():
            continue
        if s.confidence < confidence_min:
            log.info("stumble_below_floor", target=s.target, confidence=s.confidence)
            continue
        if len(s.target.split()) > _MAX_TARGET_WORDS:
            log.info("stumble_target_too_long", target=s.target)
            continue
        out.append(s.model_copy(update={"context": _clean_context(s.context)}).model_dump())
    return out


def _parse_wins(raw: Any, said: str) -> list[Document]:
    """A win is credited only to the turn that contains it; the model sometimes carries the
    previous turn's wins forward."""
    out: list[Document] = []
    said_key = target_key(said)
    for item in raw if isinstance(raw, list) else []:
        try:
            win = WinDto.model_validate(item)
        except ValidationError:
            continue
        key = target_key(win.phrase)
        if key and key in said_key:
            out.append(win.model_dump())
        else:
            log.info("win_dropped", phrase=win.phrase, said=said[:80])
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
            audio,
            mime or "audio/webm",
            language="fr",
            prompt=stt_prompt(scene.vocab, session["due_cards"]),
        )
        said = transcript.text
    else:
        said = (text or "").strip()
    if not said and pause_ms < settings.freeze_threshold_ms:
        raise BadRequest("Nothing was heard. Hold the mic and speak.", code="empty_turn")

    learner = _turn("learner", said, session["goal_progress"], pause_ms=pause_ms)
    session["turns"].append(learner)

    result = await _complete(providers, _messages(session, scene, settings))
    progress = float(result.get("goal_progress", session["goal_progress"]) or 0.0)
    progress = max(session["goal_progress"], min(1.0, progress))
    beat = _next_beat(session.get("beat", 0), result.get("beat"), len(scene.beats))
    # The last beat is the goodbye: saying it ends the scene, whatever the model reports.
    if _learner_turns(session) >= settings.scene_max_turns:
        beat = len(scene.beats) - 1
    done = bool(result.get("done", False)) or progress >= 1.0 or beat == len(scene.beats) - 1
    learner["stumbles"] = _parse_stumbles(result.get("stumbles"), settings.stumble_confidence_min)
    learner["wins"] = _parse_wins(result.get("wins"), said)
    learner["goal_progress"] = progress

    reply_text = _without_regreeting(str(result.get("reply", "")), _FR_GREETING)
    reply_en = result.get("reply_en")
    reply = _turn(
        "character",
        reply_text or "Pardon, vous pouvez répéter ?",
        progress,
        text_en=_without_regreeting(reply_en, _EN_GREETING) if isinstance(reply_en, str) else None,
    )
    session["turns"].append(reply)
    session["goal_progress"] = progress
    session["beat"] = beat
    if done:
        session["status"] = "finished"
        session["finished_at"] = _now()

    await db.sessions.update_one(
        {"_id": session["_id"]},
        {
            "$set": {
                "turns": session["turns"],
                "goal_progress": progress,
                "beat": beat,
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
        beat=beat,
        done=done,
    )
    return session


def _stumble_dtos(sid: str, turn: Document) -> list[StumbleDto]:
    """Each target can be heard; the URL is by index, as the turn's own audio is by id."""
    return [
        StumbleDto.model_validate(
            {
                **s,
                "audio_url": tts.phrase_url(
                    f"/sessions/{sid}/turns/{turn['id']}/stumbles/{i}/audio"
                ),
            }
        )
        for i, s in enumerate(turn.get("stumbles", []))
    ]


def to_dto(session: Document) -> SessionDto:
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
            stumbles=_stumble_dtos(sid, t),
            wins=[
                WinDto.model_validate(
                    {
                        **w,
                        "audio_url": tts.phrase_url(
                            f"/sessions/{sid}/wins/{quote(w['phrase'], safe='')}/audio"
                        ),
                    }
                )
                for w in t.get("wins", [])
            ],
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
        turns=turns,
    )
