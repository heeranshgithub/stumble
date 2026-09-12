"""Cards: one per (profile, target). Born from a stumble, matured by clean production in scenes."""

import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId

from app.db import Database, Document
from app.services import fsrs_engine

MASTERY_SESSIONS = 2  # produced cleanly in this many distinct scenes → mastered


def _now() -> datetime:
    return datetime.now(UTC)


def target_key(text: str) -> str:
    """Accent-insensitive, punctuation-free, lowercase: "C'est combien ?" → "cest combien"."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    ascii_only = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9 ]+", "", ascii_only).strip()


async def upsert_from_stumble(
    db: Database,
    profile_id: ObjectId,
    session: Document,
    stumble: Document,
    prompt_line_en: str | None = None,
) -> tuple[Document, bool]:
    """Returns (card, is_new). A repeat stumble on a known target is a lapse, not a new card."""
    now = _now()
    key = target_key(stumble["target"])
    existing: Document | None = await db.cards.find_one(
        {"profile_id": profile_id, "target_key": key}
    )
    if existing is not None:
        state, due = fsrs_engine.review(existing.get("fsrs"), "again", now)
        await db.cards.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "fsrs": state,
                    "due": due,
                    "updated_at": now,
                    "last_context": stumble["context"],
                    "last_session_id": session["_id"],
                    **({"context_en": stumble["context_en"]} if stumble.get("context_en") else {}),
                    "mastered": False,
                    "mastered_at": None,
                },
                "$inc": {"reps": 1, "lapses": 1},
            },
        )
        refreshed: Document | None = await db.cards.find_one({"_id": existing["_id"]})
        return refreshed or existing, False

    state, due = fsrs_engine.initial_state(stumble["type"], now)
    doc: Document = {
        "profile_id": profile_id,
        "session_id": session["_id"],
        "scene_id": session["scene_id"],
        "type": stumble["type"],
        "said": stumble["said"],
        "target": stumble["target"],
        "target_key": key,
        "context": stumble["context"],
        "prompt_line": stumble.get("prompt_line", ""),
        "prompt_line_en": prompt_line_en or None,
        "context_en": stumble.get("context_en") or None,
        "fsrs": state,
        "due": due,
        "reps": 1,
        "lapses": 0,
        "produced": 0,
        "produced_sessions": [],
        "mastered": False,
        "mastered_at": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.cards.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc, True


async def apply_win(
    db: Database, profile_id: ObjectId, session: Document, phrase: str
) -> Document | None:
    """A clean production of a known target counts as a Good review. Returns the card, if any."""
    key = target_key(phrase)
    if not key:
        return None
    cards: list[Document] = await db.cards.find({"profile_id": profile_id}).to_list(length=500)
    match = next(
        (
            c
            for c in cards
            if c["target_key"] == key or c["target_key"] in key or key in c["target_key"]
        ),
        None,
    )
    if match is None:
        return None
    now = _now()
    sessions = list(match.get("produced_sessions", []))
    if session["_id"] not in sessions:
        sessions.append(session["_id"])
    mastered = len(sessions) >= MASTERY_SESSIONS
    state, due = fsrs_engine.review(match.get("fsrs"), "good", now)
    await db.cards.update_one(
        {"_id": match["_id"]},
        {
            "$set": {
                "fsrs": state,
                "due": due,
                "updated_at": now,
                "produced_sessions": sessions,
                "mastered": mastered,
                "mastered_at": now
                if mastered and not match.get("mastered")
                else match.get("mastered_at"),
            },
            "$inc": {"produced": 1, "reps": 1},
        },
    )
    refreshed: Document | None = await db.cards.find_one({"_id": match["_id"]})
    return refreshed


async def stats(db: Database, profile_id: ObjectId, due_window: timedelta) -> dict[str, Any]:
    now = _now()
    caught = await db.cards.count_documents({"profile_id": profile_id})
    mastered = await db.cards.count_documents({"profile_id": profile_id, "mastered": True})
    due = await db.cards.count_documents(
        {"profile_id": profile_id, "mastered": False, "due": {"$lte": now + due_window}}
    )
    return {"caught": caught, "mastered": mastered, "due": due}


async def due_cards(
    db: Database, profile_id: ObjectId, due_window: timedelta, limit: int
) -> list[Document]:
    now = _now()
    cursor = (
        db.cards.find(
            {"profile_id": profile_id, "mastered": False, "due": {"$lte": now + due_window}}
        )
        .sort("due", 1)
        .limit(limit)
    )
    docs: list[Document] = await cursor.to_list(length=limit)
    return docs


async def next_review_at(db: Database, profile_id: ObjectId) -> datetime | None:
    doc: Document | None = await db.cards.find_one(
        {"profile_id": profile_id, "mastered": False}, sort=[("due", 1)]
    )
    if doc is None:
        return None
    due: datetime = doc["due"]
    return due if due.tzinfo else due.replace(tzinfo=UTC)


async def make_due_now(db: Database, profile_id: ObjectId) -> int:
    """Every unmastered card becomes due immediately. FSRS state is untouched; only `due` moves."""
    now = _now()
    result = await db.cards.update_many(
        {"profile_id": profile_id, "mastered": False, "due": {"$gt": now}},
        {"$set": {"due": now, "updated_at": now}},
    )
    return int(result.modified_count)
