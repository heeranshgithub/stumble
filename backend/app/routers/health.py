from fastapi import APIRouter

from app.models.base import ApiModel

router = APIRouter()


class HealthDto(ApiModel):
    status: str


@router.get("/health", response_model=HealthDto)
async def health() -> HealthDto:
    """Polled by the platform. Never touches the database."""
    return HealthDto(status="ok")
