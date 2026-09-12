"""Review: what's due, how a grade reschedules, and whether a spoken attempt matched."""

from datetime import UTC, datetime, timedelta

from bson import ObjectId
from bson.errors import InvalidId

from app.db import Database, Document
from app.errors import NotFound
from app.models.review import IntervalsDto, ReviewCardDto
from app.scenes.data import get_scene
from app.services import cards, fsrs_engine, tts
from app.services.cards import target_key

DUE_CAP = 12


def _now() -> datetime:
    return datetime.now(UTC)


async def get_owned_card(db: Database, profile: Document, card_id: str) -> Document:
    try:
        oid = ObjectId(card_id)
    except (InvalidId, TypeError) as exc:
        raise NotFound("Card not found.", code="card_not_found") from exc
    doc: Document | None = await db.cards.find_one({"_id": oid, "profile_id": profile["_id"]})
    if doc is None:
        raise NotFound("Card not found.", code="card_not_found")
    return doc


async def get_any_card(db: Database, card_id: str) -> Document:
    """For the audio endpoint, fetched by an <audio> element without headers."""
    try:
        oid = ObjectId(card_id)
    except (InvalidId, TypeError) as exc:
        raise NotFound("Card not found.", code="card_not_found") from exc
    doc: Document | None = await db.cards.find_one({"_id": oid})
    if doc is None:
        raise NotFound("Card not found.", code="card_not_found")
    return doc


def to_dto(card: Document) -> ReviewCardDto:
    scene = get_scene(card["scene_id"])
    now = _now()
    return ReviewCardDto(
        _id=card["_id"],
        scene_id=card["scene_id"],
        scene_title=scene.title if scene else card["scene_id"],
        scene_color=scene.color if scene else "review",
        character_name=scene.character_name if scene else "",
        type=card["type"],
        said=card.get("said", ""),
        target=card["target"],
        context=card.get("context", ""),
        prompt_line=card.get("prompt_line", ""),
        prompt_line_en=card.get("prompt_line_en"),
        context_en=card.get("context_en"),
        due=card["due"],
        reps=int(card.get("reps", 0)),
        lapses=int(card.get("lapses", 0)),
        intervals=IntervalsDto(**fsrs_engine.preview(card.get("fsrs"), now)),
        audio_url=tts.phrase_url(f"/reviews/{card['_id']}/audio"),
    )


async def due(db: Database, profile: Document, window: timedelta) -> tuple[list[Document], int]:
    docs = await cards.due_cards(db, profile["_id"], window, limit=DUE_CAP)
    total = (await cards.stats(db, profile["_id"], window))["due"]
    return docs, total


async def grade(
    db: Database, profile: Document, card: Document, rating: str
) -> tuple[Document, str]:
    now = _now()
    before: datetime = card["due"]
    state, due_at = fsrs_engine.review(card.get("fsrs"), rating, now)
    inc = {"reps": 1, "lapses": 1} if rating == "again" else {"reps": 1}
    await db.cards.update_one(
        {"_id": card["_id"]},
        {
            "$set": {"fsrs": state, "due": due_at, "updated_at": now, "last_rating": rating},
            "$inc": inc,
        },
    )
    await db.reviews.insert_one(
        {
            "profile_id": profile["_id"],
            "card_id": card["_id"],
            "rating": rating,
            "reviewed_at": now,
            "due_before": before,
            "due_after": due_at,
            "source": "review",
        }
    )
    refreshed: Document | None = await db.cards.find_one({"_id": card["_id"]})
    return refreshed or card, fsrs_engine.format_interval(due_at - now)


def matched(card: Document, heard: str) -> bool:
    want = target_key(card["target"])
    got = target_key(heard)
    return bool(want) and want in got
