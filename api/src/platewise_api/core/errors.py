"""Reusable exception type and handlers producing the standard error envelope.

Endpoints raise :class:`ApiError` (or a subclass) for intentional failures;
framework-raised ``HTTPException`` and request-validation errors are translated
into the same envelope so clients only ever parse one error shape. See
``platewise_api.schemas.errors`` for the envelope contract.
"""

import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from platewise_api.schemas.errors import ApiErrorResponse, ErrorInfo, ValidationIssue

logger = logging.getLogger(__name__)

#: Stable codes for the HTTP errors the framework raises on its own.
_HTTP_STATUS_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
    500: "internal_error",
}


class ApiError(Exception):
    """An intentional API failure carrying a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        context: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.context = context


def _envelope(
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[ValidationIssue] | None = None,
    context: dict[str, object] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ApiErrorResponse(
        error=ErrorInfo(code=code, message=message, details=details, context=context)
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers=headers,
    )


def _handle_api_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return _envelope(exc.status_code, exc.code, exc.message, context=exc.context)


def _handle_validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ValidationIssue(
            loc=[part for part in issue.get("loc", ()) if isinstance(part, str | int)],
            msg=str(issue.get("msg", "invalid")),
            type=str(issue.get("type", "value_error")),
        )
        for issue in exc.errors()
    ]
    return _envelope(422, "validation_error", "Request validation failed.", details=details)


def _handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_STATUS_CODES.get(exc.status_code, f"http_{exc.status_code}")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _envelope(exc.status_code, code, message, headers=exc.headers)


def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unexpected_api_error",
        extra={"method": request.method, "path": request.url.path},
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _envelope(500, "internal_error", "An unexpected error occurred.")


def register_exception_handlers(app: FastAPI) -> None:
    """Install the standard-envelope handlers on ``app``."""
    app.add_exception_handler(ApiError, _handle_api_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)
