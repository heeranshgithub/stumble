"""Progress and the deck: the deck shrinking is the progress bar."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

from bson import ObjectId

from app.db import Database, Document
from app.models.progress import (
    DeckCardDto,
    DeckDto,
    ProgressDto,
    SeriesPointDto,
    UnderPressureDto,
    WordState,
)
from app.scenes.data import get_scene
from app.services import cards

SERIES_DAYS = 10


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _scene_title(scene_id: str) -> str:
    scene = get_scene(scene_id)
    return scene.title if scene else scene_id.capitalize()


async def _all_cards(db: Database, profile_id: ObjectId) -> list[Document]:
    docs: list[Document] = await db.cards.find({"profile_id": profile_id}).to_list(length=2000)
    return docs


def series(
    all_cards: list[Document],
    today: date,
    days: int = SERIES_DAYS,
    reviews: list[Document] | None = None,
    due_window: timedelta = timedelta(0),
) -> list[SeriesPointDto]:
    """Cumulative caught and mastered per day, and how many cards were actually due that day.

    "Due" means the same thing here as on the tiles: not mastered, and its due date has arrived
    (within the due window). A card's due date on a past day is recovered from the review log,
    which keeps `due_before` for every grade; a card never reviewed has kept its birth due date.
    """
    log = sorted(reviews or [], key=lambda r: _aware(r["reviewed_at"]))
    by_card: dict[Any, list[Document]] = {}
    for r in log:
        by_card.setdefault(r["card_id"], []).append(r)

    def due_on(card: Document, at: datetime) -> datetime:
        # The due date in force at `at`: the value before the first review made after `at`.
        for r in by_card.get(card["_id"], []):
            if _aware(r["reviewed_at"]) > at:
                return _aware(r["due_before"])
        return _aware(card["due"])

    def mastered_by(card: Document, at: datetime) -> bool:
        return bool(card.get("mastered_at")) and _aware(card["mastered_at"]) <= at

    now = datetime.now(UTC)
    points: list[SeriesPointDto] = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        end = datetime.combine(day, datetime.max.time(), tzinfo=UTC)
        caught = sum(1 for c in all_cards if _aware(c["created_at"]) <= end)
        mastered = sum(1 for c in all_cards if mastered_by(c, end))
        # Today uses the tiles' rule (now, plus the due window that makes "tomorrow" mean the next
        # session) so the two numbers on screen agree. A past day asks whether the card had fallen
        # due by the end of that day, with no window: the window is about sessions, not history.
        horizon = now + due_window if offset == 0 else end
        due = sum(
            1
            for c in all_cards
            if _aware(c["created_at"]) <= end
            and not mastered_by(c, end)
            and due_on(c, end) <= horizon
        )
        points.append(
            SeriesPointDto(date=day.isoformat(), caught=caught, mastered=mastered, struggling=due)
        )
    return points


async def progress(db: Database, profile: Document, due_window: timedelta) -> ProgressDto:
    profile_id = profile["_id"]
    all_cards = await _all_cards(db, profile_id)
    stats = await cards.stats(db, profile_id, due_window)
    review_log: list[Document] = await db.reviews.find(
        {"profile_id": profile_id}, {"card_id": 1, "reviewed_at": 1, "due_before": 1}
    ).to_list(length=20000)

    sessions: list[Document] = await db.sessions.find(
        {"profile_id": profile_id, "status": "finished"}
    ).to_list(length=2000)
    cleared = {s["scene_id"] for s in sessions if s.get("goal_progress", 0) >= 0.999}

    under: list[UnderPressureDto] = []
    for c in sorted(
        all_cards, key=lambda c: (-int(c.get("produced", 0)), -int(c.get("lapses", 0)))
    ):
        if int(c.get("produced", 0)) == 0:
            continue
        titles: list[str] = []
        for sid in c.get("produced_sessions", []):
            doc: Document | None = await db.sessions.find_one({"_id": sid}, {"scene_id": 1})
            if doc:
                title = _scene_title(doc["scene_id"])
                if title not in titles:
                    titles.append(title)
        under.append(
            UnderPressureDto(
                target=c["target"],
                type=c["type"],
                lapses=int(c.get("lapses", 0)),
                produced_in=titles,
            )
        )
        if len(under) == 6:
            break

    return ProgressDto(
        caught=stats["caught"],
        mastered=stats["mastered"],
        due=stats["due"],
        scenes_cleared=len(cleared),
        sessions=len(sessions),
        series=series(
            all_cards, datetime.now(UTC).date(), reviews=review_log, due_window=due_window
        ),
        under_pressure=under,
    )


async def deck(db: Database, profile: Document, due_window: timedelta) -> DeckDto:
    profile_id = profile["_id"]
    all_cards = await _all_cards(db, profile_id)
    now = datetime.now(UTC)
    stats = await cards.stats(db, profile_id, due_window)

    def state(c: dict[str, Any]) -> WordState:
        if c.get("mastered"):
            return "on"
        if _aware(c["due"]) <= now + due_window:
            return "miss"
        return "off"

    # A queue, not a scatter: what's due first, then what's still being learned, then what's
    # mastered. Within a group the soonest due comes first.
    rank = {"miss": 0, "off": 1, "on": 2}
    ordered = sorted(all_cards, key=lambda c: (rank[state(c)], _aware(c["due"])))
    return DeckDto(
        cards=[
            DeckCardDto(
                id=str(c["_id"]),
                target=c["target"],
                state=state(c),
                type=c["type"],
                scene_id=c["scene_id"],
                scene_title=_scene_title(c["scene_id"]),
                context=c.get("context", ""),
                due=c["due"],
                lapses=int(c.get("lapses", 0)),
                produced=int(c.get("produced", 0)),
            )
            for c in ordered
        ],
        caught=stats["caught"],
        mastered=stats["mastered"],
        due=stats["due"],
    )
