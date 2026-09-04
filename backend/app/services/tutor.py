"""The weekly tutor brief: every stumble is a data point; a human tutor gets the patterns."""

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.db import Database, Document
from app.log import get_logger
from app.models.progress import BriefPatternDto, TutorBriefDto
from app.scenes.data import get_scene
from app.services.providers import ChatMessage
from app.services.registry import Providers

log = get_logger(__name__)

BRIEF_PROMPT = """TUTOR BRIEF. You are writing a one-page brief for a human French tutor about an \
English-speaking adult learner, based on the learner's stumble history from spoken role-play scenes.

You get JSON: cards (each a word the learner failed to produce: type, target, what they said, the \
sentence, how many times it recurred, whether they later produced it cleanly), scenes played, and \
review grades.

Find PATTERNS a tutor can act on in the first minute of a session. Group by grammar or function, \
not by word: gender agreement, avoiding a tense, freezing on numbers or prices, English fallback \
for a domain, politeness formulas, etc. Each pattern: a short title, one sentence of detail citing \
the learner's own examples, and how many cards support it. 2 to 4 patterns, strongest first.
Then STRENGTHS: 2 to 4 things the learner reliably does well (from clean productions and wins).
Then a SUGGESTED 30-MINUTE SESSION: 3 concrete activities, each one line, built on the patterns \
and using the learner's own error list.

Be specific, warm, and brief. Never invent examples not in the data. Respond with ONLY JSON:
{"patterns": [{"title": "...", "detail": "...", "count": 3}],
 "strengths": ["..."], "suggested_session": ["...", "...", "..."]}"""


def week_label(now: datetime) -> str:
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _as_text(brief: TutorBriefDto) -> str:
    lines = [f"Stumble · tutor brief · {brief.week_label}", ""]
    lines.append(f"{brief.cards_analysed} stumbles across {brief.scenes_played} scenes.")
    lines.append("")
    lines.append("PATTERNS")
    for p in brief.patterns:
        lines.append(f"- {p.title} ({p.count}): {p.detail}")
    lines.append("")
    lines.append("STRENGTHS")
    lines.extend(f"- {s}" for s in brief.strengths)
    lines.append("")
    lines.append("SUGGESTED 30-MINUTE SESSION")
    lines.extend(f"{i}. {s}" for i, s in enumerate(brief.suggested_session, 1))
    return "\n".join(lines)


def _title(scene_id: str) -> str:
    scene = get_scene(scene_id)
    return scene.title if scene else scene_id


async def _history(db: Database, profile: Document) -> dict[str, Any]:
    cards: list[Document] = await db.cards.find({"profile_id": profile["_id"]}).to_list(length=500)
    sessions: list[Document] = await db.sessions.find(
        {"profile_id": profile["_id"], "status": "finished"}, {"scene_id": 1, "goal_progress": 1}
    ).to_list(length=500)
    reviews: list[Document] = await db.reviews.find(
        {"profile_id": profile["_id"]}, {"card_id": 1, "rating": 1}
    ).to_list(length=2000)
    by_card: dict[str, list[str]] = {}
    for r in reviews:
        by_card.setdefault(str(r["card_id"]), []).append(r["rating"])
    return {
        "cards": [
            {
                "type": c["type"],
                "target": c["target"],
                "said": c.get("said", ""),
                "context": c.get("context", ""),
                "scene": _title(c["scene_id"]),
                "recurred": int(c.get("lapses", 0)),
                "produced_clean": int(c.get("produced", 0)),
                "mastered": bool(c.get("mastered")),
                "review_grades": by_card.get(str(c["_id"]), []),
            }
            for c in cards
        ],
        "scenes_played": [
            {
                "scene": _title(s["scene_id"]),
                "goal_reached": s.get("goal_progress", 0) >= 0.999,
            }
            for s in sessions
        ],
    }


async def brief(db: Database, profile: Document, providers: Providers) -> TutorBriefDto:
    now = datetime.now(UTC)
    label = week_label(now)
    cached: Document | None = await db.briefs.find_one(
        {"profile_id": profile["_id"], "week_label": label}
    )
    history = await _history(db, profile)
    n_cards = len(history["cards"])
    if cached and cached.get("cards_analysed") == n_cards:
        return TutorBriefDto.model_validate(cached["brief"])

    messages = [
        ChatMessage("system", BRIEF_PROMPT),
        ChatMessage("user", json.dumps(history, ensure_ascii=False)),
    ]
    result = await providers.chat.complete_json(messages)

    patterns: list[BriefPatternDto] = []
    for item in result.get("patterns", []) if isinstance(result.get("patterns"), list) else []:
        try:
            patterns.append(BriefPatternDto.model_validate(item))
        except ValidationError:
            continue
    strengths = [str(s) for s in result.get("strengths", []) if isinstance(s, str)]
    session = [str(s) for s in result.get("suggested_session", []) if isinstance(s, str)]

    out = TutorBriefDto(
        week_label=label,
        generated_at=now,
        cards_analysed=n_cards,
        scenes_played=len(history["scenes_played"]),
        patterns=patterns,
        strengths=strengths,
        suggested_session=session,
        as_text="",
    )
    out = out.model_copy(update={"as_text": _as_text(out)})
    await db.briefs.update_one(
        {"profile_id": profile["_id"], "week_label": label},
        {
            "$set": {
                "profile_id": profile["_id"],
                "week_label": label,
                "cards_analysed": n_cards,
                "brief": out.model_dump(),
                "generated_at": now,
            }
        },
        upsert=True,
    )
    log.info("tutor_brief", cards=n_cards, patterns=len(patterns))
    return out
