"""Dev helper: pull every unmastered card into "due now" so the review loop can be exercised today.

    uv run python scripts/make_due.py            # all profiles
    uv run python scripts/make_due.py <device>   # one device id

Reads MONGODB_URI / MONGODB_DB from backend/.env. Never run against production.
"""

import sys
from datetime import UTC, datetime, timedelta

from pymongo import MongoClient

from app.settings import Settings


def main() -> None:
    settings = Settings()
    if settings.env == "prod":
        raise SystemExit("refusing to run with ENV=prod")
    db = MongoClient(settings.mongodb_uri)[settings.mongodb_db]
    query: dict[str, object] = {"mastered": False}
    if len(sys.argv) > 1:
        profile = db.profiles.find_one({"device_id": sys.argv[1]})
        if profile is None:
            raise SystemExit(f"no profile for device {sys.argv[1]}")
        query["profile_id"] = profile["_id"]
    result = db.cards.update_many(
        query, {"$set": {"due": datetime.now(UTC) - timedelta(minutes=1)}}
    )
    print(f"{result.modified_count} card(s) now due")


if __name__ == "__main__":
    main()
