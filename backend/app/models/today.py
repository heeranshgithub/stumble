from datetime import datetime

from app.models.base import ApiModel
from app.models.scene import SceneDto


class DeckStatsDto(ApiModel):
    caught: int
    mastered: int
    due: int


class TodayDeckDto(DeckStatsDto):
    # Counts only: naming the words here would hand the review its answers.
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
