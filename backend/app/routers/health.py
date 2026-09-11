from fastapi import APIRouter, Request

from app.models.base import ApiModel
from app.services.registry import Providers
from app.settings import Settings

router = APIRouter()


class HealthDto(ApiModel):
    status: str


class ReadyDto(ApiModel):
    status: str
    providers: str
    stt: str
    llm: str
    tts: str


@router.get("/health", response_model=HealthDto)
async def health() -> HealthDto:
    """Polled by the platform. Never touches the database."""
    return HealthDto(status="ok")


@router.get("/ready", response_model=ReadyDto)
async def ready(request: Request) -> ReadyDto:
    """What this process actually runs on. No network calls; fake mode is visible, not hidden."""
    providers: Providers = request.app.state.providers
    settings: Settings = request.app.state.settings
    real = providers.mode == "real"
    return ReadyDto(
        status="ok",
        providers=providers.mode,
        stt=f"groq/{settings.groq_stt_model}" if real else "fake",
        llm=f"openrouter/{settings.openrouter_model}" if real else "fake",
        tts=f"elevenlabs/{settings.elevenlabs_model}" if real else "fake",
    )
