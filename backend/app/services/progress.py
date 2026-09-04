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


def series(all_cards: list[Document], today: date, days: int = SERIES_DAYS) -> list[SeriesPointDto]:
    """Cumulative caught and mastered per day; struggling is what's caught but not yet mastered."""
    points: list[SeriesPointDto] = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        end = datetime.combine(day, datetime.max.time(), tzinfo=UTC)
        caught = sum(1 for c in all_cards if _aware(c["created_at"]) <= end)
        mastered = sum(
            1 for c in all_cards if c.get("mastered_at") and _aware(c["mastered_at"]) <= end
        )
        points.append(
            SeriesPointDto(
                date=day.isoformat(), caught=caught, mastered=mastered, struggling=caught - mastered
            )
        )
    return points


async def progress(db: Database, profile: Document, due_window: timedelta) -> ProgressDto:
    profile_id = profile["_id"]
    all_cards = await _all_cards(db, profile_id)
    stats = await cards.stats(db, profile_id, due_window)

    sessions: list[Document] = await db.sessions.find(
        {"profile_id": profile_id, "status": "finished"}
    ).to_list(length=2000)
    cleared = {s["scene_id"] for s in sessions if s.get("goal_progress", 0) >= 0.999}
    seconds = 0
    for s in sessions:
        finished = s.get("finished_at")
        if finished:
            seconds += int((_aware(finished) - _aware(s["created_at"])).total_seconds())

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
        minutes_spoken=round(seconds / 60),
        series=series(all_cards, datetime.now(UTC).date()),
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

    ordered = sorted(all_cards, key=lambda c: _aware(c["created_at"]), reverse=True)
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
