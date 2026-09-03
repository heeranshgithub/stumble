from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import create_app
from app.settings import Settings

DEVICE = "test-device-1"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="test",
        mongodb_uri="mongodb://unused",
        mongodb_db="stumble_test",
        cors_origins="http://test",
    )


@pytest.fixture
def mock_client() -> AsyncMongoMockClient:
    return AsyncMongoMockClient()


@pytest.fixture
async def client(
    settings: Settings, mock_client: AsyncMongoMockClient
) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=settings, db_client=mock_client)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
