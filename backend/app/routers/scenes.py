from datetime import timedelta

from fastapi import APIRouter

from app.deps import DbDep, ProfileDep, SettingsDep
from app.models.scene import SceneDto
from app.scenes.data import SCENES, to_dto
from app.services import cards

router = APIRouter()


async def cleared_ids(db: DbDep, profile: ProfileDep) -> set[str]:
    out: set[str] = set()
    async for doc in db.sessions.find(
        {"profile_id": profile["_id"], "status": "finished", "goal_progress": {"$gte": 0.999}},
        {"scene_id": 1},
    ):
        out.add(doc["scene_id"])
    return out


@router.get("/scenes", response_model=list[SceneDto])
async def list_scenes(db: DbDep, profile: ProfileDep, settings: SettingsDep) -> list[SceneDto]:
    """The track: cleared scenes, the next one (with the due words it will pull on), locked ones."""
    cleared = await cleared_ids(db, profile)
    window = timedelta(hours=settings.due_window_hours)
    due = [c["target"] for c in await cards.due_cards(db, profile["_id"], window, limit=5)]
    out: list[SceneDto] = []
    next_taken = False
    for scene in SCENES:
        if scene.id in cleared:
            out.append(to_dto(scene, status="cleared"))
        elif not next_taken:
            out.append(to_dto(scene, status="next", uses_due_cards=due))
            next_taken = True
        else:
            out.append(to_dto(scene, status="locked"))
    return out
