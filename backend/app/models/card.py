from datetime import datetime

from pydantic import Field

from app.models.base import ApiModel, MongoModel
from app.models.session import StumbleDto, StumbleType, WinDto
from app.models.today import DeckStatsDto


class CardDto(MongoModel):
    scene_id: str
    type: StumbleType
    said: str
    target: str
    context: str
    prompt_line: str
    due: datetime
    reps: int
    lapses: int
    produced: int
    mastered: bool
    created_at: datetime


class DebriefStumbleDto(StumbleDto):
    card_id: str
    is_new: bool


class DebriefDto(ApiModel):
    session_id: str
    scene_id: str
    scene_title: str
    scene_color: str
    character_name: str
    goal: str
    goal_reached: bool
    goal_progress: float
    duration_s: int
    turns_spoken: int
    stumbles: list[DebriefStumbleDto] = Field(default_factory=list)
    wins: list[WinDto] = Field(default_factory=list)
    cards_added: int
    cards_relapsed: int
    next_review_at: datetime | None
    deck: DeckStatsDto
