from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.deps import DbDep, ProfileDep, SettingsDep
from app.errors import BadRequest
from app.models.progress import DeckDto, PlacementDto, ProgressDto, TutorBriefDto
from app.services import placement, progress, tutor
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


@router.post("/placement", response_model=PlacementDto)
async def post_placement(
    db: DbDep,
    profile: ProfileDep,
    request: Request,
    audio: Annotated[UploadFile | None, File()] = None,
    text: Annotated[str | None, Form()] = None,
) -> PlacementDto:
    """Onboarding: twenty seconds of anything. Places the learner and catches the first stumbles."""
    providers = _providers(request)
    if audio is not None:
        data = await audio.read()
        transcript = await providers.transcriber.transcribe(
            data, audio.content_type or "audio/webm", language="fr"
        )
        heard = transcript.text
    else:
        heard = (text or "").strip()
    if not heard:
        raise BadRequest("Nothing was said.", code="empty_placement")
    return await placement.place(db, profile, providers, heard)
