"""Which due words each scene is handed, chosen the way real use would choose them.

A learner's due words come from the scenes they've already played, so each scene gets three
targets from earlier scenes' vocabulary. Each word is labelled before any run, so the analysis
can't be fitted afterwards:

- "travels": belongs to no single place (prices, payment, time, politeness, "je peux"); any
  scene could plausibly make room for it.
- "bound": tied to the place it came from (a croissant-and-coffee word, a prescription word);
  a character forcing it in would break the role-play.
"""

from dataclasses import dataclass
from typing import Literal

Kind = Literal["travels", "bound"]


@dataclass(frozen=True)
class Target:
    word: str
    kind: Kind
    source: str  # the scene it was caught in


@dataclass(frozen=True)
class SteeringCase:
    scene: str
    targets: tuple[Target, ...]


CASES: list[SteeringCase] = [
    SteeringCase(
        "pharmacie",
        (
            Target("combien", "travels", "cafe"),
            Target("l'addition", "bound", "cafe"),
            Target("café", "bound", "cafe"),
        ),
    ),
    SteeringCase(
        "apartment",
        (
            Target("s'il vous plaît", "travels", "cafe"),
            Target("combien", "travels", "cafe"),
            Target("ordonnance", "bound", "pharmacie"),
        ),
    ),
    SteeringCase(
        "bill",
        (
            Target("mois", "travels", "apartment"),
            Target("l'addition", "bound", "cafe"),
            Target("loyer", "bound", "apartment"),
        ),
    ),
    SteeringCase(
        "doctor",
        (
            Target("mal à la tête", "travels", "pharmacie"),
            Target("rembourser", "bound", "bill"),
            Target("café", "bound", "cafe"),
        ),
    ),
    SteeringCase(
        "interview",
        (
            Target("je peux", "travels", "apartment"),
            Target("mois", "travels", "apartment"),
            Target("ordonnance", "bound", "pharmacie"),
        ),
    ),
]
