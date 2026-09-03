"""FSRS scheduling via py-fsrs. No learning steps: a card is reviewed in sessions, not minutes."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fsrs import Card, Rating, Scheduler

_scheduler = Scheduler(
    desired_retention=0.9,
    learning_steps=(),
    relearning_steps=(),
    enable_fuzzing=False,
)

RATINGS: dict[str, Rating] = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}

# The stumble is the card's birth, not a review: the card stays FSRS-new so its first real review
# gets the full spread of intervals. The stumble type only decides how soon it comes back. A freeze
# or a miss means the word wasn't there at all; a correction means it was nearly there.
INITIAL_DELAY: dict[str, timedelta] = {
    "freeze": timedelta(days=1),
    "miss": timedelta(days=1),
    "code_switch": timedelta(days=1),
    "correction": timedelta(days=2),
}

State = dict[str, Any]


def _card(state: State | None) -> Card:
    return Card.from_dict(cast(Any, state)) if state else Card()


def _due(card: Card) -> datetime:
    due: datetime = card.due
    return due if due.tzinfo else due.replace(tzinfo=UTC)


def _state(card: Card) -> State:
    return cast(State, dict(card.to_dict()))


def initial_state(stumble_type: str, now: datetime) -> tuple[State, datetime]:
    card = Card(due=now)
    return _state(card), now + INITIAL_DELAY.get(stumble_type, timedelta(days=1))


def review(state: State | None, rating: str, now: datetime) -> tuple[State, datetime]:
    card, _ = _scheduler.review_card(_card(state), RATINGS[rating], review_datetime=now)
    return _state(card), _due(card)


def preview(state: State | None, now: datetime) -> dict[str, str]:
    """Next interval per rating, as the label under each grade button."""
    out: dict[str, str] = {}
    for name in RATINGS:
        _, due = review(state, name, now)
        out[name] = format_interval(due - now)
    return out


def format_interval(delta: Any) -> str:
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 3600:
        return f"{max(1, seconds // 60)}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    days = round(seconds / 86400)
    if days < 30:
        return f"{days}d"
    return f"{round(days / 30)}mo"
