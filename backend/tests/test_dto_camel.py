"""Every DTO serializes to exact camelCase keys. This is what keeps the wire convention true."""

from datetime import UTC, datetime

from app.models.profile import ProfileDto
from app.models.scene import SceneDto
from app.models.today import DeckStatsDto, TodayDto


def test_profile_dto_keys() -> None:
    dto = ProfileDto(
        _id="507f1f77bcf86cd799439011",
        device_id="d",
        language="fr",
        created_at=datetime.now(UTC),
    )
    dumped = dto.model_dump(by_alias=True)
    assert set(dumped) == {"id", "deviceId", "language", "createdAt", "onboarded", "level"}
    assert dumped["id"] == "507f1f77bcf86cd799439011"


def test_scene_dto_keys() -> None:
    dto = SceneDto(
        id="cafe",
        title="Café",
        color="cafe",
        goal="g",
        character_name="Léa",
        character_role="barista",
        order=1,
        status="next",
    )
    assert set(dto.model_dump(by_alias=True)) == {
        "id",
        "title",
        "color",
        "goal",
        "characterName",
        "characterRole",
        "order",
        "status",
        "usesDueCards",
    }


def test_today_dto_keys() -> None:
    dto = TodayDto(
        day_number=1,
        onboarded=False,
        review_due=0,
        scene_unlocked=True,
        next_scene=None,
        deck=DeckStatsDto(caught=0, mastered=0, due=0),
    )
    assert set(dto.model_dump(by_alias=True)) == {
        "dayNumber",
        "onboarded",
        "reviewDue",
        "sceneUnlocked",
        "nextScene",
        "deck",
    }
