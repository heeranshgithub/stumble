"""Planning where a scene asks for each due word: what's kept, and what the turn is told."""

from typing import Any

from app.scenes.data import get_scene
from app.services import steering
from app.services.prompts import system_prompt
from app.services.providers import ChatMessage, ProviderError

SCENE = get_scene("pharmacie")
assert SCENE is not None


def test_a_plan_keeps_only_asked_words_in_real_beats_with_a_move() -> None:
    raw = {
        "plan": [
            {"word": "combien", "beat": 3, "move": "Don't state the price; wait to be asked."},
            {"word": "café", "beat": None, "move": ""},  # fits nowhere: never forced
            {"word": "loyer", "beat": 1, "move": "Ask about rent."},  # not a due word
            {"word": "combien", "beat": 9, "move": "Out of range."},
            {"word": "combien", "beat": 2, "move": "  "},
            "not a step",
        ]
    }
    plan = steering.parse_plan(raw, SCENE, ["combien", "café"])
    assert plan == [
        {"word": "combien", "beat": 3, "move": "Don't state the price; wait to be asked."}
    ]


def test_a_turn_is_told_only_the_move_for_its_own_beat() -> None:
    plan = [{"word": "combien", "beat": 3, "move": "Don't state the price."}]
    at_payment = system_prompt(SCENE, "relaxed", ["combien"], beat=3, steer_plan=plan)
    earlier = system_prompt(SCENE, "relaxed", ["combien"], beat=1, steer_plan=plan)
    assert 'IN THIS BEAT, so the learner says "combien": Don\'t state the price.' in at_payment
    assert "IN THIS BEAT" not in earlier
    assert "Never say one yourself" in earlier


def test_without_a_plan_the_prompt_is_unchanged() -> None:
    prompt = system_prompt(SCENE, "relaxed", ["combien"], beat=1)
    assert "create natural openings for them: combien." in prompt


async def test_a_failed_plan_lets_the_scene_go_on_unplanned() -> None:
    class Down:
        async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]:
            raise ProviderError("openrouter", "The character isn't available right now.")

    assert await steering.plan(Down(), SCENE, ["combien"]) == []
    assert await steering.plan(Down(), SCENE, []) == []
