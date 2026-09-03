from datetime import UTC, datetime, timedelta

from app.services import fsrs_engine


def test_initial_state_by_stumble_type() -> None:
    now = datetime.now(UTC)
    _, freeze_due = fsrs_engine.initial_state("freeze", now)
    correction_state, correction_due = fsrs_engine.initial_state("correction", now)
    assert timedelta(hours=20) <= freeze_due - now <= timedelta(days=2)
    assert correction_due >= freeze_due
    assert correction_state["stability"] > 0


def test_review_grows_interval() -> None:
    now = datetime.now(UTC)
    state, due1 = fsrs_engine.initial_state("code_switch", now)
    state, due2 = fsrs_engine.review(state, "good", due1)
    state, due3 = fsrs_engine.review(state, "good", due2)
    assert due2 - due1 >= timedelta(days=1)
    assert due3 - due2 > due2 - due1


def test_preview_has_all_four_labels() -> None:
    now = datetime.now(UTC)
    state, _ = fsrs_engine.initial_state("miss", now)
    labels = fsrs_engine.preview(state, now)
    assert set(labels) == {"again", "hard", "good", "easy"}
    assert all(labels.values())


def test_format_interval() -> None:
    assert fsrs_engine.format_interval(timedelta(minutes=10)) == "10m"
    assert fsrs_engine.format_interval(timedelta(hours=5)) == "5h"
    assert fsrs_engine.format_interval(timedelta(days=3)) == "3d"
    assert fsrs_engine.format_interval(timedelta(days=90)) == "3mo"
