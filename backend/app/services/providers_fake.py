"""Offline providers: run the whole loop without an API key. Also what the tests use."""

import struct
from collections.abc import AsyncIterator
from typing import Any

from app.services.providers import ChatMessage, Transcript

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

    async def transcribe(self, audio: bytes, mime: str, *, language: str) -> Transcript:
        return Transcript(text=self.text, duration_s=max(0.5, len(audio) / 32000))


class FakeChat:
    """Rule-based stand-in: recasts English words, advances the goal a third per turn."""

    async def complete_json(self, messages: list[ChatMessage]) -> dict[str, Any]:
        learner_turns = [m for m in messages if m.role == "user"]
        # The pause annotation is metadata for the model, never part of the learner's sentence.
        last = learner_turns[-1].content.split("\n\n[", 1)[0] if learner_turns else ""
        lowered = last.lower()
        stumbles: list[dict[str, Any]] = []
        for en, fr in _EN_FR.items():
            if en in lowered:
                context = _cloze(last, en)
                stumbles.append(
                    {
                        "type": "code_switch",
                        "said": en,
                        "target": fr,
                        "context": context,
                        "prompt_line": "",
                        "confidence": 0.95,
                    }
                )
        n = len(learner_turns)
        reply, reply_en = _REPLIES[min(n - 1, len(_REPLIES) - 1)] if n else _REPLIES[0]
        progress = min(1.0, round(n / 3, 2))
        return {
            "reply": reply,
            "reply_en": reply_en,
            "goal_progress": progress,
            "done": progress >= 1.0,
            "stumbles": stumbles,
            "wins": [],
        }


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

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        yield _SILENCE
