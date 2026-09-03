from datetime import UTC, datetime

from pymongo import ReturnDocument

from app.db import Database, Document


async def upsert_by_device_id(db: Database, device_id: str) -> Document:
    """First call creates the profile; every later call returns the same document."""
    doc: Document | None = await db.profiles.find_one_and_update(
        {"device_id": device_id},
        {
            "$setOnInsert": {
                "device_id": device_id,
                "language": "fr",
                "created_at": datetime.now(UTC),
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:  # pragma: no cover - upsert=True guarantees a document
        raise RuntimeError("profile upsert returned no document")
    return doc
