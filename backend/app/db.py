from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Documents are plain dicts in snake_case. They never leave a service as-is.
Document = dict[str, Any]
Database = AsyncIOMotorDatabase[Document]
Client = AsyncIOMotorClient[Document]


def make_client(uri: str) -> Client:
    return AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
