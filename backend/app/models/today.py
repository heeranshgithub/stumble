from app.models.base import ApiModel
from app.models.scene import SceneDto


class DeckStatsDto(ApiModel):
    caught: int
    mastered: int
    due: int


class TodayDto(ApiModel):
    day_number: int
    review_due: int
    next_scene: SceneDto | None
    deck: DeckStatsDto
