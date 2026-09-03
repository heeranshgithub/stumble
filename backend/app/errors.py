from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.log import get_logger
from app.middleware import request_id_of
from app.models.base import ApiModel

log = get_logger(__name__)


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict[str, Any]


class ErrorEnvelope(ApiModel):
    error: ErrorBody


class AppError(Exception):
    """Routes raise these; only this module turns them into responses."""

    status_code = 500
    code = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class BadRequest(AppError):
    status_code = 400
    code = "bad_request"


class NotFound(AppError):
    status_code = 404
    code = "not_found"


def _envelope(
    request: Request, *, code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details={"requestId": request_id_of(request), **(details or {})},
        )
    )
    return body.model_dump(by_alias=True)


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(request, code=exc.code, message=exc.message, details=exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(p) for p in e.get("loc", [])], "msg": e.get("msg", "")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_envelope(
                request,
                code="validation_error",
                message="Request failed validation.",
                details={"errors": errors},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(request, code=code, message=message),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content=_envelope(request, code="internal_error", message="Internal server error."),
        )
