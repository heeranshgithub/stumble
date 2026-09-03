from typing import Annotated

from fastapi import Depends, Header, Request

from app.db import Database, Document
from app.errors import BadRequest
from app.services.profiles import upsert_by_device_id
from app.settings import Settings

DEVICE_ID_HEADER = "X-Device-Id"


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


async def get_profile(
    db: Annotated[Database, Depends(get_db)],
    x_device_id: Annotated[str | None, Header(alias=DEVICE_ID_HEADER)] = None,
) -> Document:
    """No accounts: the device id is the identity. Missing header is a 400, never a silent guest."""
    device_id = (x_device_id or "").strip()
    if not device_id:
        raise BadRequest(f"{DEVICE_ID_HEADER} header is required.", code="device_id_required")
    return await upsert_by_device_id(db, device_id)


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Database, Depends(get_db)]
ProfileDep = Annotated[Document, Depends(get_profile)]
