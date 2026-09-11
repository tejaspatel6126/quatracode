"""
Scanner Orchestrator tests — Phase 04.

Tests the CoreScanner orchestration: module order, partial failure,
overall ScanResult structure, and security boundary.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.scanners.scanner import CoreScanner
from app.schemas.scan_result import (
    CookiesResult,
    HeadersResult,
    ModuleStatus,
    ScanStatus,
    ScannerErrorCode,
    ScannerModule,
    TLSResult,
)
from app.services.safe_http_client import SafeHTTPClient
from tests.scanners.conftest import make_https_target, make_http_target, make_response


# ── Build a mock HTTP client ───────────────────────────────────────────────────

def _mock_client(response=None, exc=None):
    client = MagicMock(spec=SafeHTTPClient)
    if exc is not None:
        client.get.side_effect = exc
    else:
        client.get.return_value = response or make_response(status_code=200)
    return client


# ── Basic scan result structure ───────────────────────────────────────────────

@patch("app.scanners.scanner.scan_tls")
@patch("app.scanners.scanner.scan_certificate")
@patch("app.scanners.scanner.scan_redirects")
def test_scan_result_has_metadata(mock_redirects, mock_cert, mock_tls):
    mock_tls.return_value = TLSResult(available=True)
    mock_cert.return_value = MagicMock(error=None)
    mock_redirects.return_value = MagicMock(available=True, error=None)

    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_https_target()
    result = scanner.scan(target)

    assert result.target_hostname == "example.com"
    assert result.target_scheme == "https"
    assert result.scanner_version == "0.4.0"
    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.started_at <= result.completed_at


def test_scan_result_has_all_module_statuses():
    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_https_target()

    with patch("app.scanners.scanner.scan_tls") as mock_tls, \
         patch("app.scanners.scanner.scan_certificate") as mock_cert, \
         patch("app.scanners.scanner.scan_redirects") as mock_redirects:
        mock_tls.return_value = TLSResult(available=True)
        mock_cert.return_value = MagicMock(error=None)
        mock_redirects.return_value = MagicMock(available=True, error=None)

        result = scanner.scan(target)

    modules = {m.module for m in result.module_statuses}
    assert ScannerModule.TLS in modules
    assert ScannerModule.CERTIFICATE in modules
    assert ScannerModule.HTTP in modules
    assert ScannerModule.HEADERS in modules
    assert ScannerModule.COOKIES in modules
    assert ScannerModule.REDIRECTS in modules


# ── Partial failure ───────────────────────────────────────────────────────────

@patch("app.scanners.scanner.scan_tls", side_effect=Exception("TLS crashed"))
@patch("app.scanners.scanner.scan_certificate")
@patch("app.scanners.scanner.scan_redirects")
def test_tls_failure_does_not_abort_scan(mock_redirects, mock_cert, mock_tls):
    """TLS failing must not abort HTTP/Header/Cookie/Redirect modules."""
    mock_cert.return_value = MagicMock(error=None)
    mock_redirects.return_value = MagicMock(available=True, error=None)

    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_https_target()
    result = scanner.scan(target)

    # Scan must not raise
    assert result is not None

    # TLS module should be FAILED
    tls_status = next(m for m in result.module_statuses if m.module == ScannerModule.TLS)
    assert tls_status.status == ModuleStatus.FAILED

    # HTTP module should still have been attempted
    http_status = next(m for m in result.module_statuses if m.module == ScannerModule.HTTP)
    # HTTP may be COMPLETED or FAILED depending on client
    assert http_status is not None


def test_partial_scan_status_when_some_fail():
    """If some modules fail and some succeed, status should be PARTIAL."""
    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_https_target()

    with patch("app.scanners.scanner.scan_tls", side_effect=Exception("crash")), \
         patch("app.scanners.scanner.scan_certificate") as mock_cert, \
         patch("app.scanners.scanner.scan_redirects") as mock_redirects:
        mock_cert.return_value = MagicMock(error=None)
        mock_redirects.return_value = MagicMock(available=True, error=None)
        result = scanner.scan(target)

    assert result.status == ScanStatus.PARTIAL


# ── No severity in orchestrator output ───────────────────────────────────────

def test_no_severity_in_scan_result():
    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_http_target()

    with patch("app.scanners.scanner.scan_tls") as mock_tls, \
         patch("app.scanners.scanner.scan_certificate") as mock_cert, \
         patch("app.scanners.scanner.scan_redirects") as mock_redirects:
        mock_tls.return_value = TLSResult(available=False)
        mock_cert.return_value = MagicMock(error=None)
        mock_redirects.return_value = MagicMock(available=True, error=None)

        result = scanner.scan(target)

    result_json = result.model_dump_json()
    assert "severity" not in result_json.lower()
    assert "risk_score" not in result_json.lower()
    assert "ai_explanation" not in result_json.lower()


# ── Module execution order is deterministic ───────────────────────────────────

def test_module_order_is_deterministic():
    call_order = []

    client = _mock_client(make_response(status_code=200))
    scanner = CoreScanner(http_client=client)
    target = make_https_target()

    with patch("app.scanners.scanner.scan_tls") as mock_tls, \
         patch("app.scanners.scanner.scan_certificate") as mock_cert, \
         patch("app.scanners.scanner.scan_http") as mock_http, \
         patch("app.scanners.scanner.scan_headers") as mock_headers, \
         patch("app.scanners.scanner.scan_cookies") as mock_cookies, \
         patch("app.scanners.scanner.scan_redirects") as mock_redirects:

        def track(name, ret):
            def fn(*a, **kw):
                call_order.append(name)
                return ret
            return fn

        mock_tls.side_effect = track("tls", TLSResult(available=True))
        mock_cert.side_effect = track("cert", MagicMock(error=None))
        mock_http.side_effect = track("http", (MagicMock(error=None), make_response()))
        mock_headers.side_effect = track("headers", HeadersResult(available=True))
        mock_cookies.side_effect = track("cookies", CookiesResult(available=True))
        mock_redirects.side_effect = track("redirects", MagicMock(available=True, error=None))

        scanner.scan(target)

    expected = ["tls", "cert", "http", "headers", "cookies", "redirects"]
    assert call_order == expected


# ── Scanner requires ValidatedTarget ─────────────────────────────────────────

def test_scanner_requires_validated_target():
    """CoreScanner.scan() requires a ValidatedTarget — not a raw string."""
    scanner = CoreScanner()
    with pytest.raises((AttributeError, TypeError)):
        scanner.scan("https://example.com")  # type: ignore[arg-type]


# ── HTTP scanner integration: headers and cookies get shared response ──────────

def test_shared_response_passed_to_header_and_cookie_scanners():
    """Headers and cookies should be analysed from the same HTTP response."""
    shared_response = make_response(
        status_code=200,
        headers={
            "set-cookie": "pref=1; Secure",
            "strict-transport-security": "max-age=3600",
        },
    )
    client = _mock_client(shared_response)
    scanner = CoreScanner(http_client=client)
    target = make_https_target()

    with patch("app.scanners.scanner.scan_tls") as mock_tls, \
         patch("app.scanners.scanner.scan_certificate") as mock_cert, \
         patch("app.scanners.scanner.scan_redirects") as mock_redirects:
        mock_tls.return_value = TLSResult(available=True)
        mock_cert.return_value = MagicMock(error=None)
        mock_redirects.return_value = MagicMock(available=True, error=None)

        result = scanner.scan(target)

    # HSTS should be observed
    assert result.headers is not None
    assert result.headers.hsts.present is True

    # Cookie should be observed
    assert result.cookies is not None
    assert len(result.cookies.cookies) == 1
    assert result.cookies.cookies[0].secure is True
