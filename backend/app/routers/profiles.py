from fastapi import APIRouter

from app.deps import DbDep, ProfileDep
from app.models.profile import ProfileDto

router = APIRouter()


@router.post("/profiles", response_model=ProfileDto)
async def create_profile(profile: ProfileDep) -> ProfileDto:
    """Idempotent: creates the profile for this device on first call, returns it afterwards."""
    return ProfileDto.model_validate(profile)


@router.post("/profiles/onboarded", response_model=ProfileDto)
async def mark_onboarded(db: DbDep, profile: ProfileDep) -> ProfileDto:
    """Leaving the intro is the onboarding. Until then, Today sends a new device to the intro."""
    await db.profiles.update_one({"_id": profile["_id"]}, {"$set": {"onboarded": True}})
    return ProfileDto.model_validate({**profile, "onboarded": True})
