"""The standard API error envelope.

Every non-2xx response body produced by the exception handlers in
``platewise_api.core.errors`` has this shape:

    {"error": {"code": ..., "message": ..., "details": ..., "context": ...}}

``code`` is machine-readable and stable; ``message`` is for humans and may
change wording freely. ``details`` carries field-level validation issues (422
only); ``context`` carries optional structured data an endpoint chooses to
attach. Clients must branch on ``code``, never on ``message``.
"""

from pydantic import BaseModel


class ValidationIssue(BaseModel):
    """One field-level problem inside a validation error."""

    loc: list[str | int]
    msg: str
    type: str


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: list[ValidationIssue] | None = None
    context: dict[str, object] | None = None


class ApiErrorResponse(BaseModel):
    error: ErrorInfo
