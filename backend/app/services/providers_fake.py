"""Offline providers: run the whole loop without an API key. Also what the tests use."""

import struct
from collections.abc import AsyncIterator
from typing import Any

from app.services.providers import Assessment, ChatMessage, Transcript

# A tiny en → fr map so the fake catches code-switches deterministically.
_EN_FR = {
    "coffee": "café",
    "milk": "lait",
    "please": "s'il vous plaît",
    "thanks": "merci",
    "thank": "merci",
    "water": "eau",
    "bread": "pain",
    "how much": "combien",
    "money": "argent",
    "sorry": "pardon",
}

_REPLIES = [
    ("Un café au lait, bien sûr ! Et avec ça ?", "A café au lait, of course! Anything else?"),
    ("Très bien. Ça fait deux euros cinquante.", "Very good. That's two euros fifty."),
    ("Merci, bonne journée !", "Thank you, have a good day!"),
]


class FakeTranscriber:
    def __init__(self, text: str = "Je voudrais un coffee au lait, s'il vous plaît.") -> None:
        self.text = text

    async def transcribe(
        self, audio: bytes, mime: str, *, language: str, prompt: str | None = None
    ) -> Transcript:
        return Transcript(text=self.text, duration_s=max(0.5, len(audio) / 32000))


_FAKE_BRIEF: dict[str, Any] = {
    "patterns": [
        {
            "title": "English fallback for café vocabulary",
            "detail": "You reached for 'coffee' and 'please' mid-sentence; the French forms exist "
            "but aren't automatic yet.",
            "count": 2,
        },
        {
            "title": "Freezes on prices",
            "detail": "You stalled when asked to pay; 'C'est combien ?' is the missing formula.",
            "count": 1,
        },
    ],
    "strengths": ["You greet and open naturally", "You keep talking after a stumble"],
    "suggested_session": [
        "Role-play a market with prices from 2 to 50 euros.",
        "Drill the five café formulas until automatic.",
        "Five minutes on 'je voudrais' + noun for ordering.",
    ],
}


class FakeChat:
    """Rule-based stand-in: recasts English words, advances the goal a third per turn."""

    async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]:
        system = next((m.content for m in messages if m.role == "system"), "")
        if system.startswith("WEEK IN REVIEW"):
            return dict(_FAKE_BRIEF)
        learner_turns = [m for m in messages if m.role == "user"]
        # The pause annotation is metadata for the model, never part of the learner's sentence.
        last = learner_turns[-1].content.split("\n\n[", 1)[0] if learner_turns else ""
        stumbles = _code_switches(last)
        n = len(learner_turns)
        reply, reply_en = _REPLIES[min(n - 1, len(_REPLIES) - 1)] if n else _REPLIES[0]
        progress = min(1.0, round(n / 3, 2))
        return {
            "reply": reply,
            "reply_en": reply_en,
            "goal_progress": progress,
            "done": progress >= 1.0,
            "stumbles": stumbles,
            "wins": [{"phrase": "s'il vous plaît"}] if "s'il vous pla" in last.lower() else [],
        }


def _code_switches(sentence: str) -> list[dict[str, Any]]:
    lowered = sentence.lower()
    out: list[dict[str, Any]] = []
    for en, fr in _EN_FR.items():
        if en in lowered:
            out.append(
                {
                    "type": "code_switch",
                    "said": en,
                    "target": fr,
                    "context": _cloze(sentence, en),
                    "prompt_line": "",
                    "confidence": 0.95,
                }
            )
    return out


def _cloze(sentence: str, word: str) -> str:
    idx = sentence.lower().find(word)
    if idx < 0:
        return sentence
    return sentence[:idx] + "___" + sentence[idx + len(word) :]


def _silent_wav(ms: int = 400, rate: int = 8000) -> bytes:
    frames = rate * ms // 1000
    data = b"\x00\x00" * frames
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        rate,
        rate * 2,
        2,
        16,
        b"data",
        len(data),
    )
    return header + data


_SILENCE = _silent_wav()


class FakeSynthesizer:
    content_type = "audio/wav"

    async def stream(self, text: str, *, speed: float = 1.0) -> AsyncIterator[bytes]:
        yield _SILENCE


# A hazard scores 0.95 when the screened text contains one of its markers, else 0.02. The
# defaults cover a few obvious words; tests pass their own to script a verdict.
_GUARD_MARKERS: dict[str, tuple[str, ...]] = {
    "harassment": ("idiot",),
    "sexual": ("sexy",),
    "violence": ("frappe", "smash"),
    "dangerous": ("drogue", "bomb"),
    "self_harm": ("mourir",),
    "sensitive_topic": ("macron",),
    "instruction_override": ("ignore",),
    "unsafe_reply": ("pathétique",),
    "broke_character": ("from now on i'll speak english",),
}


class FakeGuard:
    """Offline stand-in for Jev. Reads the learner's line on the way in and the character's reply
    on the way out, and records every call so a test can assert what was screened."""

    def __init__(self, markers: dict[str, tuple[str, ...]] | None = None) -> None:
        self._markers = _GUARD_MARKERS if markers is None else markers
        self.calls: list[dict[str, Any]] = []

    async def assess(
        self, state: dict[str, Any], questions: dict[str, dict[str, Any]]
    ) -> Assessment:
        self.calls.append(state)
        text = str(state.get("character_reply", state.get("learner_said", ""))).lower()
        answers: dict[str, dict[str, Any]] = {}
        for qid, q in questions.items():
            if q["type"] == "noul":
                hit = any(m in text for m in self._markers.get(qid, ()))
                answers[qid] = {"type": "noul", "noul": 0.95 if hit else 0.02}
            else:
                answers[qid] = {"type": "score", "score": 0.0, "confidence": 1.0}
        return Assessment(answers=answers, model="fake-guard", ms=1)
