from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.base import ApiModel, MongoModel, RequestModel

StumbleType = Literal["freeze", "code_switch", "correction", "miss"]
Patience = Literal["relaxed", "normal", "real"]


class StartSessionRequest(RequestModel):
    scene_id: str
    patience: Patience = "normal"


class StumbleDto(ApiModel):
    type: StumbleType
    said: str
    target: str
    context: str
    prompt_line: str
    confidence: float
    # The target, spoken. Set on the wire only; a stumble in the database has no URL.
    audio_url: str | None = None


class WinDto(ApiModel):
    phrase: str
    card_id: str | None = None
    # The phrase, spoken. Set on the wire only.
    audio_url: str | None = None


class TurnDto(ApiModel):
    id: str
    role: Literal["character", "learner"]
    text: str
    text_en: str | None = None
    stumbles: list[StumbleDto] = Field(default_factory=list)
    wins: list[WinDto] = Field(default_factory=list)
    goal_progress: float
    audio_url: str | None = None
    pause_ms: int = 0
    created_at: datetime


class SessionDto(MongoModel):
    scene_id: str
    scene_title: str
    scene_color: str
    character_name: str
    character_role: str
    goal: str
    patience: Patience
    goal_progress: float
    done: bool
    turns: list[TurnDto]
