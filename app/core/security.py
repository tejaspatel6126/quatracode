"""
Security middleware foundation.
Adds security response headers on every request.
Request-ID generation and injection also lives here.
"""

import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generate or propagate a unique request ID for every request.
    - Reads X-Request-ID from the incoming request if present.
    - Falls back to a newly generated UUID4.
    - Stores on request.state.request_id for use by handlers and loggers.
    - Adds X-Request-ID to every response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("X-Request-ID", "").strip()
        # Only accept safe, non-empty values (max 64 chars, no injection risk)
        if incoming and len(incoming) <= 64 and incoming.isascii():
            request_id = incoming
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Inject security headers on every response.
    CSP is deliberately permissive for Phase 01 (frontend is same-origin).
    Production hardening belongs to Phase 09/10.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        )
        # Baseline CSP — tightened in Phase 09/10
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        # NOTE: Strict-Transport-Security is intentionally omitted here.
        # It must only be sent over verified HTTPS connections (Phase 10).
        return response
