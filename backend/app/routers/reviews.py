from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import Response

from app.deps import DbDep, ProfileDep, SettingsDep
from app.errors import BadRequest
from app.models.review import AttemptDto, DueNowDto, GradeRequest, GradeResultDto, ReviewListDto
from app.services import cards, reviews, tts
from app.services.registry import Providers

router = APIRouter()


@router.get("/reviews/due", response_model=ReviewListDto)
async def due_reviews(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> ReviewListDto:
    """Due cards, oldest first, capped so a missed week never becomes a guilt pile."""
    window = timedelta(hours=settings.due_window_hours)
    docs, total = await reviews.due(db, profile, window)
    return ReviewListDto(cards=[reviews.to_dto(d) for d in docs], total_due=total)


# Declared before /reviews/{card_id}: a literal segment must win over the id parameter.
@router.post("/reviews/due-now", response_model=DueNowDto)
async def due_now(db: DbDep, profile: ProfileDep) -> DueNowDto:
    """A testing lever, not a learner feature: pull every unmastered card's due date to now.

    A new card is due tomorrow on purpose (the next session, not the same hour), which makes the
    review screen untestable within a day of playing. This is the explicit way around that,
    reachable from the profile utility screen only. Nothing else about the card changes.
    """
    return DueNowDto(cards=await cards.make_due_now(db, profile["_id"]))


@router.post("/reviews/{card_id}", response_model=GradeResultDto)
async def grade_card(
    card_id: str, body: GradeRequest, db: DbDep, profile: ProfileDep, settings: SettingsDep
) -> GradeResultDto:
    card = await reviews.get_owned_card(db, profile, card_id)
    updated, interval = await reviews.grade(db, profile, card, body.rating)
    window = timedelta(hours=settings.due_window_hours)
    remaining = (await cards.stats(db, profile["_id"], window))["due"]
    return GradeResultDto(
        card_id=str(updated["_id"]),
        rating=body.rating,
        due=updated["due"],
        interval=interval,
        remaining_due=remaining,
    )


@router.post("/reviews/{card_id}/attempt", response_model=AttemptDto)
async def attempt_card(
    card_id: str,
    db: DbDep,
    profile: ProfileDep,
    request: Request,
    audio: Annotated[UploadFile | None, File()] = None,
    text: Annotated[str | None, Form()] = None,
) -> AttemptDto:
    """A spoken (or typed) attempt at the card. Says what was heard and whether it matched."""
    card = await reviews.get_owned_card(db, profile, card_id)
    providers: Providers = request.app.state.providers
    if audio is not None:
        data = await audio.read()
        transcript = await providers.transcriber.transcribe(
            data, audio.content_type or "audio/webm", language="fr"
        )
        heard = transcript.text
    else:
        heard = (text or "").strip()
    if not heard:
        raise BadRequest("Nothing was said.", code="empty_attempt")
    return AttemptDto(heard=heard, matched=reviews.matched(card, heard))


@router.get("/reviews/{card_id}/audio")
async def card_audio(
    card_id: str,
    db: DbDep,
    request: Request,
    speed: Annotated[float, Query(ge=0.7, le=1.2)] = tts.PHRASE_SPEED,
) -> Response:
    """The target phrase, spoken. Fetched by an <audio> element, so no device header here."""
    card = await reviews.get_any_card(db, card_id)
    return await tts.stream_cached(request, f"card:{card_id}", card["target"], speed=speed)
