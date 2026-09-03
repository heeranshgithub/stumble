from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import create_app
from app.services.providers_fake import FakeChat, FakeSynthesizer, FakeTranscriber
from app.services.registry import Providers
from app.settings import Settings

DEVICE = "test-device-1"
HEADERS = {"X-Device-Id": DEVICE}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="test",
        mongodb_uri="mongodb://unused",
        mongodb_db="stumble_test",
        cors_origins="http://test",
        providers="fake",
    )


@pytest.fixture
def mock_client() -> AsyncMongoMockClient:
    return AsyncMongoMockClient()


@pytest.fixture
def providers() -> Providers:
    return Providers(FakeTranscriber(), FakeChat(), FakeSynthesizer(), "browser", "fake")


@pytest.fixture
async def client(
    settings: Settings, mock_client: AsyncMongoMockClient, providers: Providers
) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=settings, db_client=mock_client, providers=providers)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
