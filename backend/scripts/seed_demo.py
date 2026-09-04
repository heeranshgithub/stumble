"""Seed a lived-in profile: five days of scenes, 23 cards (14 mastered, 7 due, 2 learning), reviews.

    uv run python scripts/seed_demo.py                 # device id "demo-maya"
    uv run python scripts/seed_demo.py my-device-id
    uv run python scripts/seed_demo.py --reset         # wipe that profile's data first

Then open the app with ?device=<id> once; the browser adopts that identity.
The live Café scene in the demo video is recorded for real; this is the history behind it.
"""

import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database

from app.services import fsrs_engine
from app.services.cards import target_key
from app.settings import Settings

# (scene, type, said, target, context, prompt_line, days_ago, fate)
# fate: "mastered" | "due" | "learning"
CARDS: list[tuple[str, str, str, str, str, str, int, str]] = [
    ("placement", "code_switch", "twenty-eight", "vingt-huit", "J'ai ___ ans.", "", 5, "mastered"),
    (
        "cafe",
        "code_switch",
        "coffee",
        "café",
        "Je voudrais un ___ au lait.",
        "Qu'est-ce que je vous sers ?",
        5,
        "mastered",
    ),
    (
        "cafe",
        "code_switch",
        "milk",
        "au lait",
        "Un café ___, s'il vous plaît.",
        "Qu'est-ce que je vous sers ?",
        5,
        "mastered",
    ),
    (
        "cafe",
        "code_switch",
        "please",
        "s'il vous plaît",
        "Un café au lait, ___.",
        "",
        5,
        "mastered",
    ),
    ("cafe", "freeze", "", "combien", "C'est ___ ?", "Et avec ça ?", 5, "mastered"),
    (
        "cafe",
        "miss",
        "la facture",
        "l'addition",
        "Je peux avoir ___ ?",
        "Vous voulez autre chose ?",
        5,
        "mastered",
    ),
    ("cafe", "freeze", "", "par carte", "Je paie ___.", "Vous payez comment ?", 3, "due"),
    (
        "pharmacie",
        "correction",
        "mal de tête",
        "mal à la tête",
        "J'ai ___.",
        "Je peux vous aider ?",
        4,
        "mastered",
    ),
    (
        "pharmacie",
        "correction",
        "le ordonnance",
        "l'ordonnance",
        "Je n'ai pas ___.",
        "Vous avez une ordonnance ?",
        4,
        "mastered",
    ),
    ("pharmacie", "code_switch", "syrup", "sirop", "Vous avez un ___ ?", "", 4, "mastered"),
    ("pharmacie", "code_switch", "tablet", "comprimé", "Un ___ le matin ?", "", 4, "mastered"),
    (
        "pharmacie",
        "freeze",
        "",
        "combien de fois",
        "___ par jour ?",
        "Un comprimé, deux fois par jour.",
        4,
        "due",
    ),
    (
        "apartment",
        "code_switch",
        "rent",
        "loyer",
        "Le ___ est de combien ?",
        "Vous cherchez depuis longtemps ?",
        2,
        "mastered",
    ),
    ("apartment", "miss", "apartment", "appart", "L'___ est libre quand ?", "", 2, "mastered"),
    (
        "apartment",
        "code_switch",
        "fees",
        "charges",
        "Les ___ sont comprises ?",
        "Le loyer est de 900 euros.",
        2,
        "due",
    ),
    ("apartment", "freeze", "", "je peux", "___ visiter la chambre ?", "Voilà le salon.", 2, "due"),
    (
        "apartment",
        "freeze",
        "",
        "mois",
        "Le premier du ___ ?",
        "Vous voulez entrer quand ?",
        2,
        "mastered",
    ),
    (
        "bill",
        "code_switch",
        "bill",
        "facture",
        "Il y a une erreur sur ma ___.",
        "C'est à quel sujet ?",
        1,
        "due",
    ),
    ("bill", "code_switch", "refund", "rembourser", "Vous pouvez me ___ ?", "", 1, "due"),
    (
        "bill",
        "miss",
        "payement",
        "prélèvement",
        "Il y a un ___ que je ne reconnais pas.",
        "",
        1,
        "due",
    ),
    (
        "bill",
        "miss",
        "je ne sais pas",
        "je ne comprends pas",
        "___ cette ligne.",
        "",
        1,
        "learning",
    ),
    (
        "cafe",
        "correction",
        "le boulangerie",
        "la boulangerie",
        "Je vais à ___.",
        "Vous allez où après ?",
        3,
        "mastered",
    ),
    ("cafe", "correction", "au le marché", "au marché", "Je suis allé ___.", "", 3, "learning"),
]

SCENES: list[tuple[str, int, list[tuple[str, str]]]] = [
    (
        "cafe",
        5,
        [
            ("character", "Bonjour ! Qu'est-ce que je vous sers ?"),
            ("learner", "Je voudrais un coffee au lait, please."),
            ("character", "Un café au lait, bien sûr ! Et avec ça ?"),
            ("learner", "Non merci. C'est… c'est…"),
            ("character", "Deux euros cinquante. Vous payez comment ?"),
            ("learner", "Euh… par carte."),
            ("character", "Parfait. Bonne journée !"),
        ],
    ),
    (
        "pharmacie",
        4,
        [
            ("character", "Bonjour, je peux vous aider ?"),
            ("learner", "J'ai mal de tête. Vous avez un syrup ?"),
            ("character", "Un sirop ou un comprimé ? Vous avez une ordonnance ?"),
            ("learner", "Non, je n'ai pas le ordonnance. Un tablet."),
            ("character", "Un comprimé, deux fois par jour, avec de l'eau."),
            ("learner", "Merci beaucoup."),
        ],
    ),
    (
        "cafe",
        3,
        [
            ("character", "Bonjour ! Qu'est-ce que je vous sers ?"),
            ("learner", "Un café au lait, s'il vous plaît. C'est combien ?"),
            ("character", "Deux euros cinquante. Vous allez où après ?"),
            ("learner", "Je vais à le boulangerie, puis au le marché."),
            ("character", "Bonne balade !"),
        ],
    ),
    (
        "apartment",
        2,
        [
            (
                "character",
                "Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ?",
            ),
            ("learner", "Deux mois. Le rent est de combien ?"),
            ("character", "Le loyer est de 900 euros."),
            ("learner", "Les fees sont comprises ? Et… visiter la chambre ?"),
            ("character", "Oui, charges comprises. Vous voulez entrer quand ?"),
            ("learner", "Le premier du mois. L'appart est libre ?"),
            ("character", "Libre le premier. Je vous envoie le contrat."),
        ],
    ),
    (
        "bill",
        1,
        [
            ("character", "Service client, bonjour. C'est à quel sujet ?"),
            ("learner", "Il y a une erreur sur ma bill. Un payement que je ne reconnais pas."),
            (
                "character",
                "Je regarde. C'est un prélèvement de 12 euros pour l'option internationale.",
            ),
            ("learner", "Je ne sais pas cette ligne. Vous pouvez me refund ?"),
            ("character", "Je retire l'option et je vous rembourse les 12 euros."),
            ("learner", "Merci, c'est parfait."),
        ],
    ),
]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    reset = "--reset" in sys.argv
    device = args[0] if args else "demo-maya"

    settings = Settings()
    if settings.env == "prod" and not reset:
        print(
            "ENV=prod: seeding production is deliberate; pass --reset to confirm", file=sys.stderr
        )
        raise SystemExit(2)
    client: MongoClient[dict[str, Any]] = MongoClient(settings.mongodb_uri)
    db: Database[dict[str, Any]] = client[settings.mongodb_db]

    now = datetime.now(UTC)
    existing = db.profiles.find_one({"device_id": device})
    if existing:
        if not reset:
            print(f"profile {device} exists; pass --reset to replace it", file=sys.stderr)
            raise SystemExit(1)
        pid = existing["_id"]
        for coll in ("sessions", "cards", "reviews", "briefs"):
            db[coll].delete_many({"profile_id": pid})
        db.profiles.delete_one({"_id": pid})

    profile_id = ObjectId()
    created = now - timedelta(days=5, hours=2)
    db.profiles.insert_one(
        {
            "_id": profile_id,
            "device_id": device,
            "language": "fr",
            "created_at": created,
            "onboarded": True,
            "level": "A2",
            "placement": {
                "id": ObjectId(),
                "heard": "Bonjour, je m'appelle Maya, j'ai twenty-eight ans.",
                "at": created,
            },
        }
    )

    # Sessions: finished, goal reached, spread over the five days.
    session_ids: dict[tuple[str, int], ObjectId] = {}
    for scene_id, days_ago, turns in SCENES:
        started = now - timedelta(days=days_ago, hours=1, minutes=17)
        docs: list[dict[str, Any]] = []
        progress = 0.0
        for i, (role, text) in enumerate(turns):
            if role == "learner":
                progress = min(
                    1.0, round(progress + 1 / max(1, sum(1 for r, _ in turns if r == "learner")), 2)
                )
            docs.append(
                {
                    "id": ObjectId().binary.hex(),
                    "role": role,
                    "text": text,
                    "text_en": None,
                    "goal_progress": progress,
                    "created_at": started + timedelta(seconds=25 * i),
                    "stumbles": [],
                    "wins": [],
                    "pause_ms": 0,
                }
            )
        sid = ObjectId()
        session_ids[(scene_id, days_ago)] = sid
        db.sessions.insert_one(
            {
                "_id": sid,
                "profile_id": profile_id,
                "scene_id": scene_id,
                "patience": "normal",
                "status": "finished",
                "goal_progress": 1.0,
                "due_cards": [],
                "turns": docs,
                "created_at": started,
                "finished_at": started + timedelta(minutes=4, seconds=10),
            }
        )

    # Cards with real FSRS histories.
    later_sessions = sorted(session_ids.items(), key=lambda kv: -kv[0][1])
    n_mastered = n_due = n_learning = 0
    for scene_id, stype, said, target, context, prompt_line, days_ago, fate in CARDS:
        born = now - timedelta(days=days_ago, hours=1)
        state, due = fsrs_engine.initial_state(stype, born)
        reps, lapses, produced = 0, 0, 0
        produced_sessions: list[ObjectId] = []
        mastered_at: datetime | None = None
        reviews: list[dict[str, Any]] = []

        if fate == "mastered":
            # Reviewed Good when due, then produced clean in two later scenes.
            state, due = _review(reviews, state, "good", due)
            reps += 1
            for (_sc, d), sid in later_sessions:
                if d < days_ago and len(produced_sessions) < 2:
                    at = now - timedelta(days=d, hours=1)
                    state, due = fsrs_engine.review(state, "good", at)
                    produced += 1
                    reps += 1
                    produced_sessions.append(sid)
            mastered_at = now - timedelta(days=max(0, days_ago - 3), hours=1)
            n_mastered += 1
        elif fate == "due":
            if days_ago >= 3:
                state, due = _review(reviews, state, "again", due)
                reps += 1
                lapses += 1
            due = now - timedelta(hours=1)
            n_due += 1
        else:
            state, due = _review(reviews, state, "hard", due)
            reps += 1
            due = now + timedelta(days=2)
            n_learning += 1

        card_id = ObjectId()
        session_id = session_ids.get((scene_id, days_ago)) or next(iter(session_ids.values()))
        db.cards.insert_one(
            {
                "_id": card_id,
                "profile_id": profile_id,
                "session_id": session_id,
                "scene_id": scene_id,
                "type": stype,
                "said": said,
                "target": target,
                "target_key": target_key(target),
                "context": context,
                "prompt_line": prompt_line,
                "fsrs": state,
                "due": due,
                "reps": reps,
                "lapses": lapses,
                "produced": produced,
                "produced_sessions": produced_sessions,
                "mastered": fate == "mastered",
                "mastered_at": mastered_at,
                "created_at": born,
                "updated_at": now,
            }
        )
        for r in reviews:
            db.reviews.insert_one(
                {"profile_id": profile_id, "card_id": card_id, "source": "review", **r}
            )

    print(
        f"seeded {device}: {len(SCENES)} scenes, {len(CARDS)} cards "
        f"({n_mastered} mastered, {n_due} due, {n_learning} learning)"
    )
    print(f"open once with ?device={device}  e.g.  http://localhost:3001/?device={device}")


def _review(
    log: list[dict[str, Any]], state: dict[str, Any], rating: str, at: datetime
) -> tuple[dict[str, Any], datetime]:
    """A graded review at `at` (the card's due date), recorded in the review log."""
    new_state, new_due = fsrs_engine.review(state, rating, at)
    log.append({"rating": rating, "reviewed_at": at, "due_before": at, "due_after": new_due})
    return new_state, new_due


if __name__ == "__main__":
    main()
