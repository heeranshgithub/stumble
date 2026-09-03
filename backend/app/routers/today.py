from datetime import UTC, datetime

from fastapi import APIRouter

from app.deps import ProfileDep
from app.models.today import DeckStatsDto, TodayDto
from app.scenes.data import SCENES, to_dto

router = APIRouter()


def _day_number(created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return (datetime.now(UTC).date() - created_at.date()).days + 1


@router.get("/today", response_model=TodayDto)
async def today(profile: ProfileDep) -> TodayDto:
    """The home screen. Numbers become real once cards exist (day 4); the shape is final now."""
    first = SCENES[0]
    return TodayDto(
        day_number=_day_number(profile["created_at"]),
        review_due=0,
        next_scene=to_dto(first, status="next", uses_due_cards=[]),
        deck=DeckStatsDto(caught=0, mastered=0, due=0),
    )
