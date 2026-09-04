from datetime import datetime

from app.models.base import MongoModel


class ProfileDto(MongoModel):
    device_id: str
    language: str
    created_at: datetime
    onboarded: bool = False
    level: str | None = None
