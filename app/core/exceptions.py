"""
Centralized exception definitions and HTTP exception handlers.
API responses never expose tracebacks, internal paths, or secrets.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Custom application exceptions ────────────────────────────────────────────

class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__("NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__("VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service temporarily unavailable") -> None:
        super().__init__(
            "SERVICE_UNAVAILABLE", message, status.HTTP_503_SERVICE_UNAVAILABLE
        )


# ── Response builders ─────────────────────────────────────────────────────────

def error_response(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if request_id:
        body["error"]["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


# ── Exception handlers ────────────────────────────────────────────────────────

def _get_request_id(request: Request) -> Optional[str]:
    return request.state.request_id if hasattr(request.state, "request_id") else None


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "Application error: code=%s message=%s path=%s",
        exc.code,
        exc.message,
        request.url.path,
        extra={"request_id": _get_request_id(request) or "-"},
    )
    return error_response(
        code=exc.code,
        message=exc.message,
        request_id=_get_request_id(request),
        status_code=exc.status_code,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.info(
        "Request validation error: path=%s", request.url.path,
        extra={"request_id": _get_request_id(request) or "-"},
    )
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed. Check your input.",
        request_id=_get_request_id(request),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the real error server-side; never expose it in the response
    logger.exception(
        "Unhandled exception: path=%s",
        request.url.path,
        extra={"request_id": _get_request_id(request) or "-"},
    )
    return error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        request_id=_get_request_id(request),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]
