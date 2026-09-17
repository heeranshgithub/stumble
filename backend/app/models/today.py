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
    # Review comes first, and one new scene per session: the scene unlocks once nothing is due and
    # the last cleared scene is a session old.
    scene_unlocked: bool
    # When the session gate opens, if that is what's shut; None otherwise.
    scene_unlocks_at: datetime | None = None
    next_scene: SceneDto | None
    deck: TodayDeckDto
