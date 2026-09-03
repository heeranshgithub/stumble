from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.base import ApiModel, MongoModel, RequestModel
from app.models.session import StumbleType

Grade = Literal["again", "hard", "good", "easy"]


class IntervalsDto(ApiModel):
    again: str
    hard: str
    good: str
    easy: str


class ReviewCardDto(MongoModel):
    scene_id: str
    scene_title: str
    scene_color: str
    character_name: str
    type: StumbleType
    said: str
    target: str
    context: str
    prompt_line: str
    due: datetime
    reps: int
    lapses: int
    intervals: IntervalsDto
    audio_url: str


class ReviewListDto(ApiModel):
    cards: list[ReviewCardDto] = Field(default_factory=list)
    total_due: int


class GradeRequest(RequestModel):
    rating: Grade


class GradeResultDto(ApiModel):
    card_id: str
    rating: Grade
    due: datetime
    interval: str
    remaining_due: int


class AttemptDto(ApiModel):
    heard: str
    matched: bool
