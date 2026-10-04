"""Steering eval: when a scene is handed due words, does it make the learner use them?

Every scene from the pharmacy on is played to the end twice over: once with three due words from
earlier scenes (cases.py), once with none (the control), and each several times, since the models
vary. The character side is the real turn (`sessions.take_turn`: the real prompt, beats, facts and
filters) on an in-memory database, so the eval never touches Atlas. Text goes in, not audio:
steering happens in the character's replies, not in transcription. The guard is a pass-through,
since it isn't what's measured here.

The learner is a second model from another family, playing an A2 learner with the scene's goal.
It is never told the due words, so it can only say one if the conversation invites it. A third
model reads each finished transcript and answers, per word, one narrow question: did the character
create a natural opening for the learner to say it? The rest is checked in code.

Steering is the difference between the two conditions: a word that comes up anyway in the control
was never steered toward.

    uv run python -m evals.steering.run_steering --label v1
    uv run python -m evals.steering.run_steering --label v1 --runs 1 --only pharmacie
"""

import argparse
import asyncio
import json
import re
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import httpx
from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient

from app.scenes.data import Scene, get_scene
from app.services import sessions
from app.services.cards import target_key
from app.services.providers_fake import FakeGuard
from app.services.registry import build_providers
from app.settings import Settings
from evals.steering.cases import CASES, SteeringCase

RESULTS = Path(__file__).parent / "results"
OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
LEARNER_MODEL = "openai/gpt-4.1-mini"
JUDGE_MODEL = "anthropic/claude-sonnet-4.5"
MAX_LEARNER_TURNS = 14  # the app forces a last beat at 12; this only stops a runaway loop

_LEARNER = """You are a learner of French at A2 level, speaking in a role-play. {setting}
Your goal: {goal}

Reply with ONE short line in French, one or two short sentences, the way a real A2 learner talks:
simple words, the odd small mistake is fine. Answer what was just said and move toward your goal.
No narration, no quotation marks, no translation. Use English only if you are truly stuck.
When the conversation is clearly over, say a short goodbye."""

_JUDGE = """You are reading a French speaking-practice role-play between a learner and a character.
The character was supposed to steer the conversation so the learner would say certain words.

For each word or phrase below, answer one question: at any point, did the CHARACTER create a
natural opening that invites the LEARNER to say it themselves? An opening means that after the
character's line, the learner now needs that word to answer, or to get what they want: a
question whose natural answer contains it, or something left unsaid that the learner has to
ask about with it. It is NOT an opening if the character supplies the information itself (for
"combien", stating the price is not an opening: the learner no longer needs to ask), if the
character only says the word, or if the learner brings it up unprompted.

Words: {words}

Transcript (character lines are marked C, learner lines L, numbered by turn):
{transcript}

Answer as JSON only:
{{"words": [{{"word": "<word>", "opening": true or false, "turn": <turn number of the first
opening, or null>, "quote": "<the character's line that opened it, or empty>"}}]}}"""


async def _openrouter(
    client: httpx.AsyncClient, key: str, model: str, messages: list[dict[str, str]], **extra: Any
) -> str:
    body: dict[str, Any] = {"model": model, "messages": messages, **extra}
    for attempt in range(5):
        res = await client.post(
            OPENROUTER, json=body, headers={"Authorization": f"Bearer {key}"}, timeout=90
        )
        if res.status_code in (429, 500, 502, 503) and attempt < 4:
            await asyncio.sleep(2 + attempt * 3)
            continue
        res.raise_for_status()
        content: str = res.json()["choices"][0]["message"]["content"] or ""
        return content.strip()
    raise RuntimeError(f"{model}: no answer")


def _setting(scene: Scene) -> str:
    return (
        f"Scene: {scene.title}. You are the customer or candidate; the other person is "
        f"{scene.character_name}, the {scene.character_role}."
    )


async def play(
    case: SteeringCase,
    condition: str,
    run: int,
    providers: Any,
    settings: Settings,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> dict[str, Any]:
    async with sem:
        scene = get_scene(case.scene)
        assert scene is not None, case.scene
        db = AsyncMongoMockClient()["stumble_steering"]
        profile = {
            "_id": ObjectId(),
            "device_id": f"steer-{case.scene}-{condition}-{run}",
            "language": "fr",
            "onboarded": True,
            "created_at": datetime.now(UTC),
        }
        await db.profiles.insert_one(profile)
        due = [t.word for t in case.targets] if condition == "due" else []
        session = await sessions.start(db, profile, scene, "relaxed", due_cards=due)
        system = _LEARNER.format(setting=_setting(scene), goal=scene.goal)
        convo: list[dict[str, str]] = [{"role": "system", "content": system}]
        error = None
        for _ in range(MAX_LEARNER_TURNS):
            if session["status"] != "active":
                break
            convo.append({"role": "user", "content": session["turns"][-1]["text"]})
            line = await _openrouter(
                client, settings.openrouter_api_key or "", LEARNER_MODEL, convo, temperature=0.7
            )
            convo.append({"role": "assistant", "content": line})
            try:
                session = await sessions.take_turn(
                    db, providers, settings, session, audio=None, mime=None, text=line, pause_ms=0
                )
            except Exception as exc:  # a provider refusing mid-scene is itself a result
                error = f"{type(exc).__name__}: {exc}"
                break
        turns = [{"role": t["role"], "text": t["text"]} for t in session["turns"]]
        return {
            "scene": case.scene,
            "condition": condition,
            "run": run,
            "targets": [t.__dict__ for t in case.targets],
            "turns": turns,
            "goal_reached": session.get("goal_progress", 0.0) >= 0.999,
            "learner_turns": sum(t["role"] == "learner" for t in turns),
            "error": error,
        }


async def judge(
    sim: dict[str, Any], key: str, client: httpx.AsyncClient, sem: asyncio.Semaphore
) -> None:
    lines, n = [], 0
    for t in sim["turns"]:
        if t["role"] == "character":
            n += 1
            lines.append(f"{n}C: {t['text']}")
        else:
            lines.append(f"{n}L: {t['text']}")
    words = [t["word"] for t in sim["targets"]]
    prompt = _JUDGE.format(words=", ".join(f'"{w}"' for w in words), transcript="\n".join(lines))
    async with sem:
        raw = await _openrouter(
            client, key, JUDGE_MODEL, [{"role": "user", "content": prompt}], temperature=0
        )
    m = re.search(r"\{.*\}", raw, re.S)
    verdicts = {v["word"]: v for v in json.loads(m.group(0))["words"]} if m else {}
    learner = [target_key(t["text"]) for t in sim["turns"] if t["role"] == "learner"]
    character = [target_key(t["text"]) for t in sim["turns"] if t["role"] == "character"]
    out = []
    for t in sim["targets"]:
        key_ = target_key(t["word"])
        said_at = next((i + 1 for i, line in enumerate(learner) if key_ in line), None)
        v = verdicts.get(t["word"], {})
        out.append(
            {
                **t,
                "opening": bool(v.get("opening")),
                "opening_turn": v.get("turn"),
                "quote": v.get("quote", ""),
                "learner_said": said_at is not None,
                "learner_said_turn": said_at,
                "character_said": any(key_ in line for line in character),
            }
        )
    sim["words"] = out


def _rate(rows: list[dict[str, Any]], field: str) -> str:
    if not rows:
        return "-"
    hits = sum(bool(r[field]) for r in rows)
    return f"{hits}/{len(rows)} ({round(100 * hits / len(rows))}%)"


def summarise(sims: list[dict[str, Any]], label: str) -> str:
    words = [dict(w, condition=s["condition"], scene=s["scene"]) for s in sims for w in s["words"]]
    by = defaultdict(list)
    for w in words:
        by[(w["condition"],)].append(w)
        by[(w["condition"], w["kind"])].append(w)
        by[(w["condition"], w["scene"])].append(w)
    lines = [
        f"# Steering eval: {label}",
        "",
        f"{len(sims)} scenes played to the end, {datetime.now(UTC):%Y-%m-%d %H:%M} UTC. "
        f"Learner: `{LEARNER_MODEL}`. Judge: `{JUDGE_MODEL}`. Character: the app's own model.",
        "",
        "## Headline",
        "",
        "| | With due words | Control (none) |",
        "|---|---|---|",
    ]
    for field, name in [
        ("opening", "Character created an opening for the word"),
        ("learner_said", "Learner said the word"),
        ("character_said", "Character said the word itself"),
    ]:
        due_rate, control_rate = _rate(by[("due",)], field), _rate(by[("control",)], field)
        lines.append(f"| {name} | {due_rate} | {control_rate} |")
    for cond in ("due", "control"):
        cs = [s for s in sims if s["condition"] == cond]
        if cs:
            goal = sum(s["goal_reached"] for s in cs)
            turns = round(mean(s["learner_turns"] for s in cs), 1)
            lines.append(
                f"| Scenes reaching the goal ({cond}) | {goal}/{len(cs)} "
                f"| avg {turns} learner turns |"
            )
    lines += ["", "## By kind of word", "", "| Kind | Condition | Opening | Learner said |"]
    lines.append("|---|---|---|---|")
    for kind in ("travels", "bound"):
        for cond in ("due", "control"):
            rows = by[(cond, kind)]
            lines.append(
                f"| {kind} | {cond} | {_rate(rows, 'opening')} | {_rate(rows, 'learner_said')} |"
            )
    lines += ["", "## By scene", "", "| Scene | Condition | Opening | Learner said |"]
    lines.append("|---|---|---|---|")
    for case in CASES:
        for cond in ("due", "control"):
            rows = by[(cond, case.scene)]
            lines.append(
                f"| {case.scene} | {cond} | {_rate(rows, 'opening')} "
                f"| {_rate(rows, 'learner_said')} |"
            )
    lines += [
        "",
        "## Every word, with due words",
        "",
        "| Scene | Run | Word | Kind | Opening (turn) | Learner said (turn) | The opening |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in sims:
        if s["condition"] != "due":
            continue
        for w in s["words"]:
            quote = str(w["quote"]).replace("|", "\\|")[:90]
            lines.append(
                f"| {s['scene']} | {s['run']} | {w['word']} | {w['kind']} "
                f"| {'yes' if w['opening'] else 'no'} ({w['opening_turn'] or '-'}) "
                f"| {'yes' if w['learner_said'] else 'no'} ({w['learner_said_turn'] or '-'}) "
                f"| {quote} |"
            )
    errors = [s for s in sims if s["error"]]
    if errors:
        lines += ["", f"Errors: {len(errors)}"] + [f"- {s['scene']} {s['error']}" for s in errors]
    return "\n".join(lines) + "\n"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="", help="comma-separated scene ids")
    ap.add_argument("--concurrency", type=int, default=5)
    args = ap.parse_args()
    settings = Settings()
    assert settings.openrouter_api_key, "OPENROUTER_API_KEY is not set"
    providers = replace(build_providers(settings), guard=FakeGuard(markers={}))
    only = set(filter(None, args.only.split(",")))
    cases = [c for c in CASES if not only or c.scene in only]
    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient() as client:
        try:
            sims = await asyncio.gather(
                *(
                    play(c, cond, r, providers, settings, client, sem)
                    for c in cases
                    for cond in ("due", "control")
                    for r in range(1, args.runs + 1)
                )
            )
        finally:
            await providers.aclose()
        await asyncio.gather(*(judge(s, settings.openrouter_api_key, client, sem) for s in sims))
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"steering-{args.label}.json").write_text(
        json.dumps(list(sims), ensure_ascii=False, indent=2)
    )
    report = summarise(list(sims), args.label)
    (RESULTS / f"steering-{args.label}.md").write_text(report)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
