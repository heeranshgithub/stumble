from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from app.deps import DbDep, ProfileDep, SettingsDep
from app.models.scene import SceneDto
from app.models.today import DeckStatsDto, TodayDto
from app.scenes.data import SCENES, to_dto
from app.services import cards

router = APIRouter()


def _day_number(created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return (datetime.now(UTC).date() - created_at.date()).days + 1


async def next_scene(db: DbDep, profile: ProfileDep, due_window: timedelta) -> SceneDto | None:
    """First scene not yet cleared. Cleared = a finished session that reached the goal."""
    cleared: set[str] = set()
    async for doc in db.sessions.find(
        {"profile_id": profile["_id"], "status": "finished", "goal_progress": {"$gte": 0.999}},
        {"scene_id": 1},
    ):
        cleared.add(doc["scene_id"])
    scene = next((s for s in SCENES if s.id not in cleared), None)
    if scene is None:
        return None
    due = await cards.due_cards(db, profile["_id"], due_window, limit=5)
    return to_dto(scene, status="next", uses_due_cards=[c["target"] for c in due])


@router.get("/today", response_model=TodayDto)
async def today(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> TodayDto:
    """The home screen: what's due, what's next, how the deck is doing."""
    window = timedelta(hours=settings.due_window_hours)
    deck = await cards.stats(db, profile["_id"], window)
    return TodayDto(
        day_number=_day_number(profile["created_at"]),
        review_due=deck["due"],
        next_scene=await next_scene(db, profile, window),
        deck=DeckStatsDto(**deck),
    )
