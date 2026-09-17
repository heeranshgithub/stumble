"""The track: which scene is next, and whether it is open.

Two gates, both server-side so the Scenes tab can't route around Today:
- Review first: nothing may be due. A due word is reviewed before a new scene is played.
- One new scene per session: the last cleared scene must be at least a session old. Without this a
  learner could clear all six in an hour with café-level French; the scenes climb on purpose.
Cleared scenes are always replayable; that's where due words get steered into a scene.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.db import Database, Document
from app.scenes.data import SCENES, Scene
from app.services import cards


def _now() -> datetime:
    return datetime.now(UTC)


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass(frozen=True)
class Track:
    cleared: set[str]
    next: Scene | None
    due: int
    # When the session gate opens; None when it already has, or there is no next scene.
    unlocks_at: datetime | None

    @property
    def unlocked(self) -> bool:
        return self.next is not None and self.due == 0 and self.unlocks_at is None

    def playable(self, scene: Scene) -> bool:
        return scene.id in self.cleared or (
            self.next is not None and scene.id == self.next.id and self.unlocked
        )


async def load(db: Database, profile: Document, session_gap: timedelta) -> Track:
    cleared: set[str] = set()
    last_cleared_at: datetime | None = None
    async for doc in db.sessions.find(
        {"profile_id": profile["_id"], "status": "finished", "goal_progress": {"$gte": 0.999}},
        {"scene_id": 1, "finished_at": 1},
    ):
        cleared.add(doc["scene_id"])
        at = doc.get("finished_at")
        if at is not None and (last_cleared_at is None or _utc(at) > last_cleared_at):
            last_cleared_at = _utc(at)
    nxt = next((s for s in SCENES if s.id not in cleared), None)
    due = (await cards.stats(db, profile["_id"], session_gap))["due"]
    unlocks_at: datetime | None = None
    if nxt is not None and last_cleared_at is not None:
        opens = last_cleared_at + session_gap
        if opens > _now():
            unlocks_at = opens
    return Track(cleared=cleared, next=nxt, due=due, unlocks_at=unlocks_at)


async def skip_to_tomorrow(db: Database, profile: Document, session_gap: timedelta) -> int:
    """For testing: the last scene counts as a session ago, so the track opens without waiting."""
    boundary = _now() - session_gap
    result = await db.sessions.update_many(
        {"profile_id": profile["_id"], "status": "finished", "finished_at": {"$gt": boundary}},
        {"$set": {"finished_at": boundary}},
    )
    return int(result.modified_count)
