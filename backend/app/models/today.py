from datetime import datetime

from pydantic import Field

from app.models.base import ApiModel
from app.models.progress import WordState
from app.models.scene import SceneDto


class DeckWordDto(ApiModel):
    target: str
    state: WordState


class DeckStatsDto(ApiModel):
    caught: int
    mastered: int
    due: int


class TodayDeckDto(DeckStatsDto):
    # A glimpse of the deck for the home screen: due first, then learning, then mastered.
    words: list[DeckWordDto] = Field(default_factory=list)
    # When the next not-yet-due card comes back; None when nothing is waiting.
    next_due: datetime | None = None


class TodayDto(ApiModel):
    day_number: int
    onboarded: bool
    review_due: int
    # Review comes first: the scene unlocks once nothing is due, so reviewed words get produced.
    scene_unlocked: bool
    next_scene: SceneDto | None
    deck: TodayDeckDto
