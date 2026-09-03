"""The lifespan runs for real in production and never in the other tests; exercise it once here."""

from mongomock_motor import AsyncMongoMockClient

from app.main import create_app
from app.services.registry import Providers, build_providers
from app.settings import Settings


async def test_lifespan_starts_and_stops(
    settings: Settings, mock_client: AsyncMongoMockClient, providers: Providers
) -> None:
    app = create_app(settings=settings, db_client=mock_client, providers=providers)
    async with app.router.lifespan_context(app):
        assert app.state.db is not None
        assert app.state.providers.mode == "fake"


def test_fake_mode_needs_no_keys(settings: Settings) -> None:
    built = build_providers(settings)
    assert built.mode == "fake"
    assert built.tts_provider == "browser"


def test_auto_mode_without_keys_is_fake_and_tells_client_to_use_browser_tts() -> None:
    built = build_providers(Settings(env="test", providers="auto"))
    assert built.mode == "fake"
    assert built.tts_provider == "browser"
