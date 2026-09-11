"""
Redirect Scanner — Phase 04.

Inspects redirect behavior — specifically HTTP→HTTPS enforcement.

CRITICAL SECURITY RULE:
  Every redirect destination passes through Phase 03 validate_target()
  before any connection is attempted. The SafeHTTPClient already enforces
  this — this scanner MUST use SafeHTTPClient, never direct httpx calls.

What this scanner does:
  - For HTTP targets: check if they redirect to HTTPS
  - Record the full redirect chain (URLs, status codes, hop count)
  - Detect redirect loops and limit exceedance
  - Block unsafe redirect destinations (via SafeHTTPClient → validate_target)

What it does NOT do:
  - Assign severity (Phase 05)
  - Follow redirects beyond SafeHTTPClient's configured MAX_REDIRECTS
  - Allow unsafe destination (private/loopback/metadata)
"""

import logging

from app.schemas.scan_result import (
    RedirectStep,
    RedirectsResult,
    ScannerError,
    ScannerErrorCode,
)
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.target_validator import ValidatedTarget
from app.services.safe_http_client import SafeHTTPClient, SafeResponse

logger = logging.getLogger(__name__)

# HTTP status codes that indicate a redirect
_REDIRECT_CODES: frozenset[int] = frozenset({301, 302, 303, 307, 308})


def scan_redirects(
    target: ValidatedTarget,
    client: SafeHTTPClient | None = None,
) -> RedirectsResult:
    """
    Inspect redirect chain from the target URL.

    The SafeHTTPClient handles redirect following and Phase 03 revalidation.
    This scanner interprets the final result to produce raw observations.

    Parameters
    ----------
    target : ValidatedTarget
        Phase 03 validated target.
    client : SafeHTTPClient, optional
        Inject mock for tests.

    Returns
    -------
    RedirectsResult
        Raw redirect chain observations.
    """
    if client is None:
        client = SafeHTTPClient()

    initial_url = target.normalized_url
    logger.info("Redirect scan: initial_url=%r scheme=%r", initial_url, target.scheme)

    try:
        response = client.get(target)

        final_url = response.final_url
        final_scheme = _extract_scheme(final_url) if final_url else target.scheme
        https_redirect_observed = (
            target.scheme == "http"
            and final_scheme == "https"
            and response.redirect_count > 0
        )

        # Build a simplified redirect chain from the response metadata.
        # SafeHTTPClient does not currently expose per-step details externally;
        # we record what we know: initial, final, count.
        redirect_chain = _build_chain(initial_url, final_url, response)

        return RedirectsResult(
            available=True,
            initial_url=initial_url,
            final_url=final_url,
            final_scheme=final_scheme,
            redirect_count=response.redirect_count,
            redirect_chain=redirect_chain,
            https_redirect_observed=https_redirect_observed,
        )

    except TargetSecurityError as exc:
        logger.warning("Redirect scan security error: code=%s", exc.code)
        error_code = _map_error(exc.code)
        return RedirectsResult(
            available=False,
            initial_url=initial_url,
            error=ScannerError(
                code=error_code,
                message=exc.message,
            ),
        )

    except Exception as exc:
        logger.warning("Redirect scan unexpected error: %s", type(exc).__name__)
        return RedirectsResult(
            available=False,
            initial_url=initial_url,
            error=ScannerError(
                code=ScannerErrorCode.REDIRECT_ERROR,
                message="Unexpected error during redirect inspection.",
            ),
        )


def _build_chain(
    initial_url: str,
    final_url: str | None,
    response: SafeResponse,
) -> list[RedirectStep]:
    """
    Build a minimal redirect chain from available response metadata.

    SafeHTTPClient currently exposes redirect_count and final_url.
    If no redirects, return empty list.
    """
    if response.redirect_count == 0:
        return []

    # We have at minimum: initial→final with redirect_count hops.
    # Record what we can observe.
    chain: list[RedirectStep] = []

    if initial_url and final_url and initial_url != final_url:
        chain.append(RedirectStep(
            step=1,
            from_url=initial_url,
            status_code=response.status_code,  # status of the final response
            location=final_url,
        ))

    return chain


def _extract_scheme(url: str) -> str:
    """Extract scheme from URL string. Returns empty string on failure."""
    try:
        idx = url.index("://")
        return url[:idx].lower()
    except (ValueError, AttributeError):
        return ""


def _map_error(sec_code: str) -> ScannerErrorCode:
    _mapping: dict[str, ScannerErrorCode] = {
        SecurityCode.UNSAFE_REDIRECT:              ScannerErrorCode.REDIRECT_ERROR,
        SecurityCode.TIMEOUT:                      ScannerErrorCode.TIMEOUT,
        SecurityCode.CONNECTION_ERROR:             ScannerErrorCode.NETWORK_ERROR,
        SecurityCode.RESPONSE_SIZE_LIMIT_EXCEEDED: ScannerErrorCode.RESPONSE_TOO_LARGE,
        SecurityCode.PRIVATE_IP_BLOCKED:           ScannerErrorCode.REDIRECT_ERROR,
        SecurityCode.LOOPBACK_BLOCKED:             ScannerErrorCode.REDIRECT_ERROR,
        SecurityCode.METADATA_IP_BLOCKED:          ScannerErrorCode.REDIRECT_ERROR,
        SecurityCode.LINK_LOCAL_BLOCKED:           ScannerErrorCode.REDIRECT_ERROR,
    }
    return _mapping.get(sec_code, ScannerErrorCode.REDIRECT_ERROR)
