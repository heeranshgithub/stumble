from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Client, make_client
from app.errors import register_handlers
from app.log import configure_logging, get_logger
from app.middleware import RequestIdMiddleware
from app.routers import health, profiles, sessions, today
from app.services.audio_cache import AudioCache
from app.services.registry import Providers, build_providers
from app.settings import Settings

# Quick tunnels get a new hostname on every restart; in dev, allow them all.
_DEV_ORIGIN_REGEX = r"https://.*\.trycloudflare\.com"


def create_app(
    settings: Settings | None = None,
    db_client: Client | None = None,
    providers: Providers | None = None,
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.env)
    log = get_logger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        owns_client = db_client is None
        client = db_client or make_client(settings.mongodb_uri)
        app.state.db = client[settings.mongodb_db]
        owns_providers = providers is None
        app.state.providers = providers or build_providers(settings)
        log.info("startup", provider_mode=app.state.providers.mode, **settings.redact())
        try:
            yield
        finally:
            if owns_providers:
                await app.state.providers.aclose()
            if owns_client:
                client.close()

    app = FastAPI(title="Stumble API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.audio_cache = AudioCache()
    if db_client is not None:
        # Tests inject a client and providers and never run lifespan.
        app.state.db = db_client[settings.mongodb_db]
    if providers is not None:
        app.state.providers = providers

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=_DEV_ORIGIN_REGEX if settings.env == "dev" else None,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.add_middleware(RequestIdMiddleware)
    register_handlers(app)

    app.include_router(health.router)
    app.include_router(profiles.router)
    app.include_router(today.router)
    app.include_router(sessions.router)
    return app


app = create_app()
