"""Mastery: two clean scenes, or a memory FSRS rates months deep — and what a lapse undoes."""

from datetime import UTC, datetime, timedelta

from bson import ObjectId
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.services import cards
from tests.conftest import HEADERS

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
DB = "stumble_test"


# --- the rule itself -------------------------------------------------------


def test_two_distinct_scenes_master_a_card() -> None:
    mastered, at = cards.mastery({}, [ObjectId(), ObjectId()], {"stability": 2.3}, NOW)
    assert mastered and at == NOW


def test_one_scene_is_not_enough() -> None:
    mastered, at = cards.mastery({}, [ObjectId()], {"stability": 2.3}, NOW)
    assert not mastered and at is None


def test_recall_alone_masters_once_the_memory_is_deep() -> None:
    """The point of the change: a word the scenes never steer toward can still graduate."""
    assert cards.mastery({}, [], {"stability": cards.MASTERY_STABILITY_DAYS}, NOW)[0]
    assert not cards.mastery({}, [], {"stability": cards.MASTERY_STABILITY_DAYS - 1}, NOW)[0]


def test_a_new_card_has_no_stability_and_is_not_mastered() -> None:
    assert not cards.mastery({}, [], {"stability": None}, NOW)[0]
    assert not cards.mastery({}, [], None, NOW)[0]


def test_mastered_at_is_kept_once_set() -> None:
    earlier = datetime(2025, 12, 1, tzinfo=UTC)
    card = {"mastered": True, "mastered_at": earlier}
    assert cards.mastery(card, [ObjectId(), ObjectId()], None, NOW)[1] == earlier


def test_losing_mastery_clears_the_date() -> None:
    card = {"mastered": True, "mastered_at": NOW}
    assert cards.mastery(card, [], {"stability": 3.0}, NOW) == (False, None)


# --- what a lapse undoes ---------------------------------------------------


async def _scene(client: AsyncClient, text: str, scene: str = "cafe") -> str:
    res = await client.post("/sessions", json={"sceneId": scene}, headers=HEADERS)
    sid: str = res.json()["id"]
    await client.post(f"/sessions/{sid}/turns", data={"text": text}, headers=HEADERS)
    await client.post(f"/sessions/{sid}/finish", headers=HEADERS)
    return sid


async def _card(mock_client: AsyncMongoMockClient, target: str = "s'il vous plaît") -> dict:
    doc = await mock_client[DB].cards.find_one({"target_key": cards.target_key(target)})
    assert doc is not None
    return dict(doc)


async def test_a_stumble_clears_the_mastery_evidence(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    """Regression: `mastered: False` alone left produced_sessions behind, so a single clean
    production re-mastered the card instead of the two distinct scenes it asks for."""
    await _scene(client, "Je voudrais un coffee au lait, please.")  # births the cards
    await _scene(client, "Un café, s'il vous plaît.")  # win 1
    await _scene(client, "Encore un, s'il vous plaît.")  # win 2 → mastered
    doc = await _card(mock_client)
    assert doc["mastered"] is True
    assert len(doc["produced_sessions"]) == 2

    # Break it: saying "please" again code-switches onto the same target, which is a lapse.
    await _scene(client, "Un café, please.")
    broken = await _card(mock_client)
    assert broken["mastered"] is False
    assert broken["produced_sessions"] == [], "the evidence must reset, not just the flag"


async def test_a_win_after_a_lapse_does_not_instantly_remaster(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    await _scene(client, "Je voudrais un coffee au lait, please.")
    await _scene(client, "Un café, s'il vous plaît.")
    await _scene(client, "Encore un, s'il vous plaît.")
    doc = await _card(mock_client)
    assert doc["mastered"] is True

    # Simulate the lapse the stumble path performs, then produce it cleanly once.
    await mock_client[DB].cards.update_one(
        {"_id": doc["_id"]},
        {"$set": {"mastered": False, "mastered_at": None, "produced_sessions": []}},
    )
    await _scene(client, "Voilà, s'il vous plaît.")
    after = await _card(mock_client)
    assert after["mastered"] is False, "one clean scene must not re-master a lapsed card"
    assert len(after["produced_sessions"]) == 1


# --- the review log --------------------------------------------------------


async def test_a_scene_win_writes_a_review_log_row(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    """Without this row the progress chart has no history for a card matured only in scenes."""
    await _scene(client, "Je voudrais un coffee au lait, please.")
    await _scene(client, "Un café, s'il vous plaît.")
    rows = await mock_client[DB].reviews.find({"source": "win"}).to_list(length=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["rating"] == "good"
    assert row["due_before"] is not None and row["due_after"] is not None
    assert row["due_after"] > row["due_before"]
    assert row["profile_id"] and row["card_id"]


async def test_win_rows_do_not_steer_the_next_scene(
    client: AsyncClient, mock_client: AsyncMongoMockClient
) -> None:
    """scene_targets reads only graded reviews; a win must not feed itself back as a target."""
    await _scene(client, "Je voudrais un coffee au lait, please.")
    await _scene(client, "Un café, s'il vous plaît.")
    doc = await _card(mock_client)
    await mock_client[DB].cards.update_many({}, {"$set": {"due": datetime(2099, 1, 1, tzinfo=UTC)}})
    targets = await cards.scene_targets(
        mock_client[DB], doc["profile_id"], due_window=timedelta(hours=8), limit=5
    )
    assert targets == []


# --- what the log row buys the chart ---------------------------------------


def test_the_chart_sees_history_for_a_card_matured_only_in_scenes() -> None:
    """The reason apply_win logs a row. due_on() walks the log for a card's past due dates; with
    no rows it falls through to today's due date and the card reads as never-due on every past day.
    """
    from datetime import date

    from app.services import progress

    today = date(2026, 1, 20)
    born = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)
    card: dict = {
        "_id": ObjectId(),
        "created_at": born,
        "due": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),  # far future, after two wins
        "mastered": False,
        "mastered_at": None,
    }
    # It fell due on the 11th and sat there until a scene win on the 13th cleared it. The row that
    # win now writes is the only record that the 11th and 12th were days it was waiting on you.
    win_rows = [
        {
            "card_id": card["_id"],
            "reviewed_at": datetime(2026, 1, 13, 9, 0, tzinfo=UTC),
            "due_before": datetime(2026, 1, 11, 9, 0, tzinfo=UTC),
        }
    ]

    blind = {p.date: p.struggling for p in progress.series([card], today, reviews=[])}
    seeing = {p.date: p.struggling for p in progress.series([card], today, reviews=win_rows)}

    # Without the row the chart falls through to today's due date and sees nothing.
    assert blind["2026-01-11"] == 0 and blind["2026-01-12"] == 0
    assert seeing["2026-01-11"] == 1 and seeing["2026-01-12"] == 1
    # Cleared on the 13th, so it stops counting from then on.
    assert seeing["2026-01-13"] == 0
