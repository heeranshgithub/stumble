import logging

import structlog


def configure_logging(env: str) -> None:
    """JSON in prod, console everywhere else. Request id is bound per request in middleware."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if env == "prod" else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
