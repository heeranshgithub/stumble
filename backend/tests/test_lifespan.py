"""The lifespan runs for real in production and never in the other tests; exercise it once here."""

import pytest
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


def test_fake_mode_is_explicit_and_needs_no_keys(settings: Settings) -> None:
    built = build_providers(settings)
    assert built.mode == "fake"


def test_real_mode_is_the_default_and_refuses_to_start_without_keys() -> None:
    # No silent downgrade: a missing key stops the process and names what is missing.
    bare = Settings(
        _env_file=None,
        env="test",
        groq_api_key=None,
        openrouter_api_key=None,
        elevenlabs_api_key=None,
    )
    assert bare.providers == "real"
    with pytest.raises(RuntimeError, match="PROVIDERS=real but missing: GROQ_API_KEY, OPENROUTER"):
        build_providers(bare)
