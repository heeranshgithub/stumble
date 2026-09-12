"""Cards made before translations existed get theirs: the English of the line they answered and
of their sentence with the slot fixed. A few model calls per profile, never at review time.

    uv run python scripts/backfill_translations.py            # every profile
    uv run python scripts/backfill_translations.py demo-maya  # one
"""

import asyncio
import json
import sys
from typing import Any

import httpx
from pymongo import MongoClient
from pymongo.database import Database

from app.services.providers import ChatMessage
from app.services.providers_real import OpenRouterChat
from app.settings import Settings

PROMPT = (
    "You translate short French learner material into natural English. You get a JSON list of "
    'items, each with an "id", a "prompt" (a line a character said, may be empty) and a '
    '"sentence" (the learner\'s corrected sentence). Return ONLY JSON: '
    '{"items": [{"id": "...", "prompt_en": "...", "sentence_en": "..."}]}. '
    "Empty prompt → empty prompt_en. Keep the register; no explanations."
)
BATCH = 8  # the chat call caps output at 700 tokens; eight items fit with room to spare


async def translate(chat: OpenRouterChat, cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for start in range(0, len(cards), BATCH):
        items = [
            {
                "id": str(c["_id"]),
                "prompt": c.get("prompt_line", ""),
                "sentence": c.get("context", "___").replace("___", c["target"]),
            }
            for c in cards[start : start + BATCH]
        ]
        result = await chat.complete_json(
            [
                ChatMessage("system", PROMPT),
                ChatMessage("user", json.dumps(items, ensure_ascii=False)),
            ]
        )
        for i in result.get("items", []):
            if isinstance(i, dict):
                out[str(i.get("id"))] = i
    return out


async def main() -> None:
    settings = Settings()
    db: Database[dict[str, Any]] = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    only = sys.argv[1] if len(sys.argv) > 1 else None
    profiles = list(db.profiles.find({"device_id": only} if only else {}))
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0)) as client:
        chat = OpenRouterChat(client, settings.openrouter_api_key or "", settings.openrouter_model)
        for p in profiles:
            missing = {"$or": [{"context_en": None}, {"context_en": {"$exists": False}}]}
            cards = list(db.cards.find({"profile_id": p["_id"], **missing}))
            if not cards:
                continue
            by_id = await translate(chat, cards)
            n = 0
            for c in cards:
                t = by_id.get(str(c["_id"]))
                if not t:
                    continue
                db.cards.update_one(
                    {"_id": c["_id"]},
                    {
                        "$set": {
                            "context_en": (t.get("sentence_en") or "").strip() or None,
                            "prompt_line_en": (t.get("prompt_en") or "").strip() or None,
                        }
                    },
                )
                n += 1
            print(f"{p['device_id']}: {n}/{len(cards)} cards translated")


if __name__ == "__main__":
    asyncio.run(main())
