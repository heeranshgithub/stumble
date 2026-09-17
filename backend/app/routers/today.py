from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from app.deps import DbDep, ProfileDep, SettingsDep
from app.models.today import TodayDeckDto, TodayDto
from app.scenes.data import to_dto
from app.services import cards, progress, track

router = APIRouter()


def _day_number(created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return (datetime.now(UTC).date() - created_at.date()).days + 1


@router.get("/today", response_model=TodayDto)
async def today(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> TodayDto:
    """The home screen: what's due, what's next, how the deck is doing."""
    window = timedelta(hours=settings.due_window_hours)
    deck = await cards.stats(db, profile["_id"], window)
    full = await progress.deck(db, profile, window)
    upcoming = [c.due for c in full.cards if c.state == "off"]
    t = await track.load(db, profile, window)
    next_scene = None
    if t.next is not None:
        due = await cards.due_cards(db, profile["_id"], window, limit=5)
        next_scene = to_dto(
            t.next,
            status="next",
            uses_due_cards=[c["target"] for c in due],
            unlocked=t.unlocked,
            unlocks_at=t.unlocks_at,
        )
    return TodayDto(
        day_number=_day_number(profile["created_at"]),
        onboarded=bool(profile.get("onboarded", False)),
        review_due=deck["due"],
        scene_unlocked=t.unlocked,
        scene_unlocks_at=t.unlocks_at,
        next_scene=next_scene,
        deck=TodayDeckDto(
            **deck,
            next_due=min(upcoming) if upcoming else None,
        ),
    )
