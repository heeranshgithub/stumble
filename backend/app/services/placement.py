"""Onboarding: twenty seconds of anything in French. Place the learner, catch the first stumbles."""

from datetime import UTC, datetime
from typing import Any, Literal

from bson import ObjectId
from pydantic import ValidationError

from app.db import Database, Document
from app.models.progress import PlacementDto
from app.models.session import StumbleDto
from app.services import cards
from app.services.providers import ChatMessage
from app.services.registry import Providers

PLACEMENT_PROMPT = """PLACEMENT. An English-speaking adult said something in French for about \
twenty seconds, unprompted, to place themselves. You get the transcript.

1. Estimate their level: A1, A2 or B1. Be generous; this decides the first scene's difficulty, not \
a grade.
2. Log stumbles exactly as in a scene: code_switch (an English word inside French), correction (a \
wrong form), miss (a French word used with the wrong meaning). Each with "said", "target", and \
"context" (their sentence with the target slot as ___). Only confident ones.
3. One warm sentence of note for the learner, in English, about what you heard.

Respond with ONLY JSON:
{"level": "A2", "note": "...", "stumbles": [{"type": "code_switch", "said": "twenty-eight",
 "target": "vingt-huit", "context": "J'ai ___ ans.", "prompt_line": "", "confidence": 0.95}]}"""

LEVELS = {"A1", "A2", "B1"}


async def place(db: Database, profile: Document, providers: Providers, heard: str) -> PlacementDto:
    result = await providers.chat.complete_json(
        [ChatMessage("system", PLACEMENT_PROMPT), ChatMessage("user", heard)]
    )
    raw_level = str(result.get("level", "A2")).upper()
    level: Literal["A1", "A2", "B1"] = (
        "A1" if raw_level == "A1" else "B1" if raw_level == "B1" else "A2"
    )

    now = datetime.now(UTC)
    placement_id = ObjectId()
    pseudo_session: Document = {"_id": placement_id, "scene_id": "placement"}
    stumbles: list[StumbleDto] = []
    added = 0
    raw: Any = result.get("stumbles", [])
    for item in raw if isinstance(raw, list) else []:
        try:
            s = StumbleDto.model_validate(item)
        except ValidationError:
            continue
        if not s.target.strip():
            continue
        stumbles.append(s)
        _, is_new = await cards.upsert_from_stumble(
            db, profile["_id"], pseudo_session, s.model_dump()
        )
        added += int(is_new)

    await db.profiles.update_one(
        {"_id": profile["_id"]},
        {
            "$set": {
                "onboarded": True,
                "level": level,
                "placement": {"id": placement_id, "heard": heard, "at": now},
            }
        },
    )
    return PlacementDto(
        level=level,
        heard=heard,
        note=str(result.get("note", "")) or "Good. Let's find the words you're missing.",
        stumbles=stumbles,
        cards_added=added,
    )
