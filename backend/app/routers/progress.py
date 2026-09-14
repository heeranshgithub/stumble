from datetime import timedelta

from fastapi import APIRouter, Request

from app.deps import DbDep, ProfileDep, SettingsDep
from app.models.progress import DeckDto, ProgressDto, TutorBriefDto
from app.services import progress, tutor
from app.services.registry import Providers

router = APIRouter()


def _providers(request: Request) -> Providers:
    providers: Providers = request.app.state.providers
    return providers


@router.get("/progress", response_model=ProgressDto)
async def get_progress(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> ProgressDto:
    """Totals and the ten-day series. The struggling line staying flat is the whole story."""
    return await progress.progress(db, profile, timedelta(hours=settings.due_window_hours))


@router.get("/deck", response_model=DeckDto)
async def get_deck(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> DeckDto:
    """Every card, newest first, with its lyric state: on (mastered), off (learning), miss (due)."""
    return await progress.deck(db, profile, timedelta(hours=settings.due_window_hours))


@router.get("/tutor-brief", response_model=TutorBriefDto)
async def get_tutor_brief(db: DbDep, profile: ProfileDep, request: Request) -> TutorBriefDto:
    """The weekly one-pager for a human tutor. Cached per week until new cards appear."""
    return await tutor.brief(db, profile, _providers(request))
