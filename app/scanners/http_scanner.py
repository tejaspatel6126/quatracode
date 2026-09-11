"""
HTTP Scanner — Phase 04.

Uses ONLY the Phase 03 SafeHTTPClient — no direct httpx/requests calls.

Responsibilities:
  - Perform a HEAD (fallback to GET) request via SafeHTTPClient
  - Collect status code, final URL, content-type, server header
  - Make raw response headers available to sub-scanners

DOES NOT:
  - Parse security headers (HeaderScanner's job)
  - Parse cookies (CookieScanner's job)
  - Follow unsafe redirects (SafeHTTPClient enforces Phase 03 boundary)
  - Assign severity
"""

import logging

from app.schemas.scan_result import (
    HTTPResult,
    ScannerError,
    ScannerErrorCode,
)
from app.security.errors import TargetSecurityError
from app.security.target_validator import ValidatedTarget
from app.services.safe_http_client import SafeHTTPClient, SafeResponse

logger = logging.getLogger(__name__)


def scan_http(
    target: ValidatedTarget,
    client: SafeHTTPClient | None = None,
) -> tuple[HTTPResult, SafeResponse | None]:
    """
    Perform HTTP inspection of the target.

    Returns (HTTPResult, raw_response).
    raw_response is None on failure (so sub-scanners must guard for None).

    The raw response is passed to HeaderScanner and CookieScanner to
    avoid duplicate network requests.

    Parameters
    ----------
    target : ValidatedTarget
        Phase 03 validated target.
    client : SafeHTTPClient, optional
        Inject a mock client for tests. Production uses a new instance.

    Returns
    -------
    tuple[HTTPResult, SafeResponse | None]
    """
    if client is None:
        client = SafeHTTPClient()

    logger.info("HTTP scan: hostname=%r scheme=%r", target.hostname, target.scheme)

    try:
        response = client.get(target)

        result = HTTPResult(
            available=True,
            status_code=response.status_code,
            final_url=response.final_url,
            content_type=response.headers.get("content-type"),
            server=response.headers.get("server"),
            redirect_count=response.redirect_count,
        )
        logger.info(
            "HTTP scan: status=%d final_url=%r redirects=%d",
            response.status_code, response.final_url, response.redirect_count,
        )
        return result, response

    except TargetSecurityError as exc:
        logger.warning("HTTP scan security error: code=%s", exc.code)
        error_code = _map_security_error(exc.code)
        return (
            HTTPResult(
                available=False,
                error=ScannerError(
                    code=error_code,
                    message=exc.message,
                ),
            ),
            None,
        )

    except Exception as exc:
        logger.warning("HTTP scan unexpected error: %s", type(exc).__name__)
        return (
            HTTPResult(
                available=False,
                error=ScannerError(
                    code=ScannerErrorCode.HTTP_ERROR,
                    message="Unexpected HTTP error during scan.",
                ),
            ),
            None,
        )


def _map_security_error(sec_code: str) -> ScannerErrorCode:
    """Map Phase 03 security error codes to Phase 04 scanner error codes."""
    _mapping: dict[str, ScannerErrorCode] = {
        "TIMEOUT":                      ScannerErrorCode.TIMEOUT,
        "CONNECTION_ERROR":             ScannerErrorCode.NETWORK_ERROR,
        "RESPONSE_SIZE_LIMIT_EXCEEDED": ScannerErrorCode.RESPONSE_TOO_LARGE,
        "UNSAFE_REDIRECT":              ScannerErrorCode.REDIRECT_ERROR,
    }
    return _mapping.get(sec_code, ScannerErrorCode.HTTP_ERROR)
