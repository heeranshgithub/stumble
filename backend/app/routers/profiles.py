from fastapi import APIRouter

from app.deps import ProfileDep
from app.models.profile import ProfileDto

router = APIRouter()


@router.post("/profiles", response_model=ProfileDto)
async def create_profile(profile: ProfileDep) -> ProfileDto:
    """Idempotent: creates the profile for this device on first call, returns it afterwards."""
    return ProfileDto.model_validate(profile)
