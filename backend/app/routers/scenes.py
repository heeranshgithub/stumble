from datetime import timedelta

from fastapi import APIRouter

from app.deps import DbDep, ProfileDep, SettingsDep
from app.models.scene import SceneDto
from app.scenes.data import SCENES, to_dto
from app.services import cards, track

router = APIRouter()


@router.get("/scenes", response_model=list[SceneDto])
async def list_scenes(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> list[SceneDto]:
    """The track: cleared scenes, the next one (with the due words it will pull on), locked ones."""
    window = timedelta(hours=settings.due_window_hours)
    t = await track.load(db, profile, window)
    due = [c["target"] for c in await cards.due_cards(db, profile["_id"], window, limit=5)]
    out: list[SceneDto] = []
    for scene in SCENES:
        if scene.id in t.cleared:
            out.append(to_dto(scene, status="cleared"))
        elif t.next is not None and scene.id == t.next.id:
            out.append(
                to_dto(
                    scene,
                    status="next",
                    uses_due_cards=due,
                    unlocked=t.unlocked,
                    unlocks_at=t.unlocks_at,
                )
            )
        else:
            out.append(to_dto(scene, status="locked"))
    return out
