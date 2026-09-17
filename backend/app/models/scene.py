from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.base import ApiModel

SceneStatus = Literal["cleared", "next", "locked"]


class SceneDto(ApiModel):
    id: str
    title: str
    color: str
    goal: str
    character_name: str
    character_role: str
    order: int
    status: SceneStatus
    uses_due_cards: list[str] = Field(default_factory=list)
    # The next scene can be "next" and still shut: a review is due, or the last scene was cleared
    # less than a session ago. Cleared scenes are always open.
    unlocked: bool = True
    unlocks_at: datetime | None = None
