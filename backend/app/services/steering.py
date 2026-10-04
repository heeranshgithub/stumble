"""Planning how a scene gets the learner to say their due words.

A single instruction to "create openings" for the due words was measured to do almost nothing
(evals/steering): the character follows the beats, which are concrete, and lets a list of words
go. So once the words are known, at scene start, one call places each word in the beat where it
fits and writes the concrete move the character makes there. Each turn is then told only the move
for its own beat. A word that fits no beat gets none: forcing one in reads badly, and the measured
aside attempt was awkward.
"""

from typing import Any

from pydantic import BaseModel, ValidationError

from app.db import Document
from app.log import get_logger
from app.scenes.data import Scene
from app.services.providers import ChatMessage, ChatModel, ProviderError

log = get_logger(__name__)

_MAX_MOVE_CHARS = 300

_PLANNER = """You plan a French speaking-practice role-play so the learner gets to SAY certain \
words. The learner plays the customer or candidate; the character is {name}, the {role}.
Scene: {title}. The learner's goal: {goal}.
The character's beats, in order:
{beats}
Facts the character knows: {facts}.
Words the learner should say: {words}.

For each word, pick the ONE beat where the character can most naturally create the need for the
learner to say it, and write the move the character makes in that beat: a question that only
that word answers, or information the character leaves out so the learner has to ask for it
using that word (for "combien": don't state the price, wait to be asked). The move must stay in
role and fit the scene. The character never says the word itself. If a word fits no beat
naturally, its beat is null: never force it.

Answer as JSON only:
{{"plan": [{{"word": "<word>", "beat": <beat number or null>, "move": "<one sentence, in
English, telling the character what to do in that beat>"}}]}}"""


class _Step(BaseModel):
    word: str
    beat: int | None = None
    move: str = ""


def parse_plan(raw: Any, scene: Scene, words: list[str]) -> list[Document]:
    """Keeps only steps for words that were asked for, in a real beat, with a move."""
    items = raw.get("plan") if isinstance(raw, dict) else None
    out: list[Document] = []
    for item in items if isinstance(items, list) else []:
        try:
            step = _Step.model_validate(item)
        except ValidationError:
            log.warning("steer_step_dropped", item=item)
            continue
        if step.word not in words or step.beat is None:
            continue
        if not 0 <= step.beat < len(scene.beats) or not step.move.strip():
            log.info("steer_step_out_of_range", word=step.word, beat=step.beat)
            continue
        out.append({"word": step.word, "beat": step.beat, "move": step.move[:_MAX_MOVE_CHARS]})
    return out


async def plan(chat: ChatModel, scene: Scene, words: list[str]) -> list[Document]:
    """One call per scene, made when it starts. A failure is logged and the scene goes on
    unplanned: the plan helps the practice, the scene doesn't depend on it."""
    if not words:
        return []
    prompt = _PLANNER.format(
        name=scene.character_name,
        role=scene.character_role,
        title=scene.title,
        goal=scene.goal,
        beats="\n".join(f"{i}: {b}" for i, b in enumerate(scene.beats)),
        facts="; ".join(scene.facts),
        words=", ".join(f'"{w}"' for w in words),
    )
    try:
        raw = await chat.complete_json([ChatMessage("user", prompt)])
    except ProviderError as exc:
        log.warning("steer_plan_failed", scene=scene.id, error=exc.message)
        return []
    steps = parse_plan(raw, scene, words)
    log.info("steer_plan", scene=scene.id, words=words, planned=[s["word"] for s in steps])
    return steps
