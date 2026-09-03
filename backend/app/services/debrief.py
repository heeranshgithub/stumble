"""Finishing a scene: verdict, cards from stumbles, wins against known cards. Idempotent."""

from datetime import UTC, datetime, timedelta

from app.db import Database, Document
from app.models.card import DebriefDto, DebriefStumbleDto
from app.models.session import WinDto
from app.models.today import DeckStatsDto
from app.scenes.data import get_scene
from app.services import cards
from app.services.cards import target_key

GOAL_REACHED_AT = 0.999


async def finish(
    db: Database, profile: Document, session: Document, due_window: timedelta
) -> DebriefDto:
    if session.get("debrief"):
        return DebriefDto.model_validate(session["debrief"])

    scene = get_scene(session["scene_id"])
    if scene is None:  # pragma: no cover - scenes are code
        raise ValueError("unknown scene")
    now = datetime.now(UTC)
    profile_id = profile["_id"]

    # One card per target per scene, first occurrence wins the context.
    seen: set[str] = set()
    stumbles: list[DebriefStumbleDto] = []
    added = relapsed = 0
    for turn in session["turns"]:
        if turn["role"] != "learner":
            continue
        for s in turn.get("stumbles", []):
            key = target_key(s["target"])
            if not key or key in seen:
                continue
            seen.add(key)
            card, is_new = await cards.upsert_from_stumble(db, profile_id, session, s)
            added += int(is_new)
            relapsed += int(not is_new)
            stumbles.append(DebriefStumbleDto(**s, card_id=str(card["_id"]), is_new=is_new))

    wins: list[WinDto] = []
    seen_wins: set[str] = set()
    for turn in session["turns"]:
        for w in turn.get("wins", []):
            key = target_key(w["phrase"])
            if not key or key in seen or key in seen_wins:
                continue
            seen_wins.add(key)
            won = await cards.apply_win(db, profile_id, session, w["phrase"])
            wins.append(WinDto(phrase=w["phrase"], card_id=str(won["_id"]) if won else None))

    turns_spoken = sum(1 for t in session["turns"] if t["role"] == "learner")
    started: datetime = session["created_at"]
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    deck = await cards.stats(db, profile_id, due_window)
    debrief = DebriefDto(
        session_id=str(session["_id"]),
        scene_id=scene.id,
        scene_title=scene.title,
        scene_color=scene.color,
        character_name=scene.character_name,
        goal=scene.goal,
        goal_reached=session["goal_progress"] >= GOAL_REACHED_AT,
        goal_progress=session["goal_progress"],
        duration_s=int((now - started).total_seconds()),
        turns_spoken=turns_spoken,
        stumbles=stumbles,
        wins=wins,
        cards_added=added,
        cards_relapsed=relapsed,
        next_review_at=await cards.next_review_at(db, profile_id),
        deck=DeckStatsDto(**deck),
    )
    await db.sessions.update_one(
        {"_id": session["_id"]},
        {
            "$set": {
                "status": "finished",
                "finished_at": session.get("finished_at") or now,
                "debrief": debrief.model_dump(),
            }
        },
    )
    return debrief
