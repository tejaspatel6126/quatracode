"""
Redirect Scanner tests — Phase 04.

Mocks SafeHTTPClient — no real network connections.
Verifies Phase 03 security boundary is enforced for redirects.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.scanners.redirect_scanner import scan_redirects
from app.schemas.scan_result import RedirectsResult, ScannerErrorCode
from app.security.errors import TargetSecurityError, SecurityCode
from app.services.safe_http_client import SafeResponse
from tests.scanners.conftest import make_https_target, make_http_target, make_response


def _make_client(response: SafeResponse | None = None, exc: Exception | None = None):
    """Build a mock SafeHTTPClient."""
    client = MagicMock()
    if exc is not None:
        client.get.side_effect = exc
    else:
        client.get.return_value = response
    return client


# ── No redirect ───────────────────────────────────────────────────────────────

def test_no_redirect():
    target = make_https_target()
    response = make_response(
        status_code=200,
        final_url="https://example.com/",
        redirect_count=0,
    )
    client = _make_client(response)
    result = scan_redirects(target, client=client)

    assert result.available is True
    assert result.redirect_count == 0
    assert result.https_redirect_observed is False


# ── HTTP → HTTPS redirect ─────────────────────────────────────────────────────

def test_http_to_https_redirect_observed():
    target = make_http_target()  # scheme=http
    response = make_response(
        status_code=200,
        final_url="https://example.com/",
        redirect_count=1,
    )
    client = _make_client(response)
    result = scan_redirects(target, client=client)

    assert result.available is True
    assert result.https_redirect_observed is True
    assert result.final_scheme == "https"
    assert result.redirect_count == 1


def test_https_to_https_no_redirect_observation():
    """Starting from HTTPS, https_redirect_observed should be False."""
    target = make_https_target()
    response = make_response(
        status_code=200,
        final_url="https://www.example.com/",
        redirect_count=1,
    )
    client = _make_client(response)
    result = scan_redirects(target, client=client)
    # https_redirect_observed only set when initial scheme was http
    assert result.https_redirect_observed is False


# ── Redirect chain recorded ───────────────────────────────────────────────────

def test_redirect_chain_built():
    target = make_http_target()
    response = make_response(
        status_code=200,
        final_url="https://example.com/",
        redirect_count=1,
    )
    client = _make_client(response)
    result = scan_redirects(target, client=client)
    assert result.redirect_count == 1
    assert len(result.redirect_chain) > 0


# ── Redirect limit exceeded ───────────────────────────────────────────────────

def test_redirect_limit_exceeded_structured():
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.UNSAFE_REDIRECT,
        message="Too many redirects (max 10).",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.REDIRECT_ERROR


# ── Unsafe redirect blocked (Phase 03 enforcement) ────────────────────────────

@pytest.mark.parametrize("blocked_code", [
    SecurityCode.PRIVATE_IP_BLOCKED,
    SecurityCode.LOOPBACK_BLOCKED,
    SecurityCode.LINK_LOCAL_BLOCKED,
    SecurityCode.METADATA_IP_BLOCKED,
])
def test_unsafe_redirect_blocked_by_phase03(blocked_code):
    """Redirect to private/loopback/link-local/metadata must be blocked."""
    target = make_http_target()
    exc = TargetSecurityError(
        code=blocked_code,
        message="Unsafe redirect destination blocked.",
    )
    # SafeHTTPClient raises TargetSecurityError → wrapped as REDIRECT_ERROR
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.REDIRECT_ERROR


def test_redirect_to_private_ip_blocked():
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.UNSAFE_REDIRECT,
        message="Redirect destination failed security validation.",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False
    assert result.error is not None


# ── Timeout ───────────────────────────────────────────────────────────────────

def test_redirect_timeout_structured():
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.TIMEOUT,
        message="The request timed out.",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.TIMEOUT


# ── Response too large ────────────────────────────────────────────────────────

def test_response_too_large_structured():
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.RESPONSE_SIZE_LIMIT_EXCEEDED,
        message="Response exceeds maximum size.",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.RESPONSE_TOO_LARGE


# ── Malformed Location ────────────────────────────────────────────────────────

def test_redirect_missing_location_blocked():
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.UNSAFE_REDIRECT,
        message="Redirect response missing Location header.",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False


# ── Unsupported scheme redirect ───────────────────────────────────────────────

def test_unsupported_scheme_redirect_blocked():
    """Redirect to file://, ftp://, etc. must be blocked by Phase 03."""
    target = make_http_target()
    exc = TargetSecurityError(
        code=SecurityCode.UNSAFE_REDIRECT,
        message="Redirect destination failed security validation.",
    )
    client = _make_client(exc=exc)
    result = scan_redirects(target, client=client)
    assert result.available is False


# ── Initial URL recorded ──────────────────────────────────────────────────────

def test_initial_url_recorded():
    target = make_http_target()
    response = make_response(
        status_code=200,
        final_url="http://example.com/",
        redirect_count=0,
    )
    client = _make_client(response)
    result = scan_redirects(target, client=client)
    assert result.initial_url == "http://example.com/"


# ── No severity in output ─────────────────────────────────────────────────────

def test_no_severity_in_redirect_output():
    target = make_http_target()
    response = make_response(status_code=200, final_url="http://example.com/")
    client = _make_client(response)
    result = scan_redirects(target, client=client)
    result_json = result.model_dump_json()
    assert "severity" not in result_json.lower()
