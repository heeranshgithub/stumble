from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.base import ApiModel
from app.models.session import StumbleDto, StumbleType

WordState = Literal["on", "off", "miss"]


class SeriesPointDto(ApiModel):
    date: str  # YYYY-MM-DD
    caught: int
    mastered: int
    struggling: int


class UnderPressureDto(ApiModel):
    target: str
    type: StumbleType
    lapses: int
    produced_in: list[str] = Field(default_factory=list)


class ProgressDto(ApiModel):
    caught: int
    mastered: int
    due: int
    scenes_cleared: int
    sessions: int
    minutes_spoken: int
    series: list[SeriesPointDto] = Field(default_factory=list)
    under_pressure: list[UnderPressureDto] = Field(default_factory=list)


class DeckCardDto(ApiModel):
    id: str
    target: str
    state: WordState
    type: StumbleType
    scene_id: str
    scene_title: str
    context: str
    due: datetime
    lapses: int
    produced: int


class DeckDto(ApiModel):
    cards: list[DeckCardDto] = Field(default_factory=list)
    caught: int
    mastered: int
    due: int


class BriefPatternDto(ApiModel):
    title: str
    detail: str
    count: int


class TutorBriefDto(ApiModel):
    week_label: str
    generated_at: datetime
    cards_analysed: int
    scenes_played: int
    patterns: list[BriefPatternDto] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    suggested_session: list[str] = Field(default_factory=list)
    as_text: str


class PlacementDto(ApiModel):
    level: Literal["A1", "A2", "B1"]
    heard: str
    note: str
    stumbles: list[StumbleDto] = Field(default_factory=list)
    cards_added: int
