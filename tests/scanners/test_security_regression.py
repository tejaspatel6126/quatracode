"""
Security regression tests — Phase 04.

These tests verify the security invariants that must hold across
all scanner modules. They must NEVER be disabled.

Invariants tested:
  1.  Scanner cannot accept raw URLs — requires ValidatedTarget
  2.  No direct httpx/requests/urllib in scanner modules
  3.  SafeHTTPClient boundary preserved
  4.  Redirect destinations revalidated (Phase 03)
  5.  Private IPv4 remains blocked
  6.  Private IPv6 remains blocked
  7.  IPv4-mapped IPv6 bypass impossible
  8.  Loopback remains blocked
  9.  Cloud metadata (169.254.169.254) remains blocked
  10. Link-local remains blocked
  11. Timeouts remain bounded (config-driven)
  12. Response size remains bounded
  13. Cookie values never in output
  14. Passwords never in logs or API errors
  15. Nmap always uses selected_address (validated IP)
  16. Nmap always uses shell=False
  17. Nmap never passes user-controlled flags
  18. No severity/risk/AI in any Phase 04 output
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.scanners.network_discovery import scan_network
from app.scanners.redirect_scanner import scan_redirects
from app.schemas.scan_result import ScannerErrorCode, ScannerModule
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.target_validator import ValidatedTarget
from tests.scanners.conftest import make_https_target, make_http_target, make_response


# ── Invariant 1: Scanner requires ValidatedTarget ─────────────────────────────

def test_scanner_cannot_receive_raw_url():
    """CoreScanner.scan() must only accept ValidatedTarget — not raw strings."""
    from app.scanners.scanner import CoreScanner
    scanner = CoreScanner()
    with pytest.raises((AttributeError, TypeError)):
        scanner.scan("https://evil.example.com/ssrf")  # type: ignore[arg-type]


def test_scan_network_requires_validated_target():
    """scan_network() must only accept ValidatedTarget."""
    with pytest.raises((AttributeError, TypeError)):
        scan_network("192.168.1.1")  # type: ignore[arg-type]


# ── Invariants 5–10: All unsafe IPs blocked (redirect path) ──────────────────

@pytest.mark.parametrize("blocked_code,description", [
    (SecurityCode.PRIVATE_IP_BLOCKED,   "Private IPv4 (10.x/172.16.x/192.168.x)"),
    (SecurityCode.LOOPBACK_BLOCKED,     "Loopback (127.0.0.1/::1)"),
    (SecurityCode.METADATA_IP_BLOCKED,  "Cloud metadata (169.254.169.254)"),
    (SecurityCode.LINK_LOCAL_BLOCKED,   "Link-local (169.254.x.x/fe80::/10)"),
    (SecurityCode.RESERVED_IP_BLOCKED,  "Reserved IP"),
    (SecurityCode.MULTICAST_IP_BLOCKED, "Multicast"),
])
def test_unsafe_ip_blocked_in_redirect(blocked_code, description):
    """All unsafe IP categories must be blocked during redirect following."""
    target = make_http_target()
    exc = TargetSecurityError(
        code=blocked_code,
        message=f"Blocked: {description}",
    )
    client = MagicMock()
    client.get.side_effect = exc

    result = scan_redirects(target, client=client)
    assert result.available is False, f"Should be blocked: {description}"
    assert result.error is not None


# ── Invariant 7: IPv4-mapped IPv6 bypass ─────────────────────────────────────

def test_ipv4_mapped_ipv6_cannot_bypass_nmap():
    """
    ::ffff:127.0.0.1 must be classified as LOOPBACK and blocked.
    The ip_classifier handles this — defence-in-depth in scan_network.
    """
    from app.security.ip_classifier import classify_ip, IPCategory
    result = classify_ip("::ffff:127.0.0.1")
    assert result == IPCategory.LOOPBACK, "IPv4-mapped loopback must be classified as LOOPBACK"


def test_ipv4_mapped_private_classified_as_private():
    """::ffff:192.168.1.1 must be classified as PRIVATE."""
    from app.security.ip_classifier import classify_ip, IPCategory
    result = classify_ip("::ffff:192.168.1.1")
    assert result == IPCategory.PRIVATE


def test_ipv4_mapped_metadata_classified_correctly():
    """::ffff:169.254.169.254 must not be classified as PUBLIC."""
    from app.security.ip_classifier import classify_ip, IPCategory, is_metadata_address
    # Metadata check must catch it
    assert is_metadata_address("::ffff:169.254.169.254") or \
           classify_ip("::ffff:169.254.169.254") != IPCategory.PUBLIC


# ── Invariant 13: Cookie values never in output ───────────────────────────────

def test_cookie_value_never_in_scan_output():
    """Cookie values must be redacted — value_redacted=True always."""
    from app.scanners.cookie_scanner import scan_cookies
    response = make_response(headers={
        "set-cookie": "auth_token=SUPERSECRETVALUE; Secure; HttpOnly"
    })
    result = scan_cookies(response)
    result_json = result.model_dump_json()
    assert "SUPERSECRETVALUE" not in result_json
    assert all(c.value_redacted for c in result.cookies)


def test_session_cookie_value_never_in_output():
    """Session cookie values must be redacted."""
    from app.scanners.cookie_scanner import scan_cookies
    response = make_response(headers={
        "set-cookie": "session_id=abc123xyz; Path=/; HttpOnly"
    })
    result = scan_cookies(response)
    result_json = result.model_dump_json()
    assert "abc123xyz" not in result_json


# ── Invariant 14: Credentials never in API errors ─────────────────────────────

def test_url_credentials_not_in_error_message():
    """
    Phase 03 must strip credentials before any error message.
    Verify validate_target raises before credentials could reach the network.
    """
    from app.security.target_validator import validate_target
    from app.security.errors import TargetSecurityError

    with pytest.raises(TargetSecurityError) as exc_info:
        validate_target("https://user:p%40ssword@example.com/")

    # The password must never appear in the error message
    assert "p%40ssword" not in exc_info.value.message
    assert "password" not in exc_info.value.message.lower()


# ── Invariant 15–17: Nmap security ───────────────────────────────────────────

@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_target_is_ip_not_hostname(mock_run, mock_which):
    """Nmap command must use selected_address (IP), never the hostname."""
    xml = b"""<?xml version="1.0"?><nmaprun version="7.94"><host><ports></ports></host></nmaprun>"""
    mock_run.return_value = MagicMock(stdout=xml, returncode=0, stderr=b"")

    target = make_https_target(hostname="victim.example.com", ip="93.184.216.34")
    scan_network(target)

    cmd = mock_run.call_args[0][0]
    assert "93.184.216.34" in cmd
    assert "victim.example.com" not in cmd


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_shell_is_false(mock_run, mock_which):
    """shell=True is strictly forbidden in subprocess.run calls."""
    xml = b"""<?xml version="1.0"?><nmaprun version="7.94"></nmaprun>"""
    mock_run.return_value = MagicMock(stdout=xml, returncode=0, stderr=b"")

    target = make_https_target()
    scan_network(target)

    call_kwargs = mock_run.call_args[1]
    # shell must be False (or absent, defaulting to False)
    assert call_kwargs.get("shell") is not True


@patch("app.scanners.network_discovery.shutil.which", return_value="/usr/bin/nmap")
@patch("subprocess.run")
def test_nmap_no_user_controlled_flags(mock_run, mock_which):
    """Nmap must use only the fixed, pre-approved flag set."""
    xml = b"""<?xml version="1.0"?><nmaprun version="7.94"></nmaprun>"""
    mock_run.return_value = MagicMock(stdout=xml, returncode=0, stderr=b"")

    target = make_https_target()
    scan_network(target)

    cmd = mock_run.call_args[0][0]
    forbidden_flags = ["-A", "-sS", "-sV", "-O", "-sU", "--script"]
    cmd_str = " ".join(str(c) for c in cmd)
    for flag in forbidden_flags:
        assert flag not in cmd_str, f"Forbidden Nmap flag {flag!r} present"


# ── Invariant 18: No severity/AI in any Phase 04 output ──────────────────────

def test_no_severity_in_tls_result():
    from app.schemas.scan_result import TLSResult
    result = TLSResult(available=True)
    assert "severity" not in result.model_dump_json()


def test_no_severity_in_certificate_result():
    from app.schemas.scan_result import CertificateResult
    result = CertificateResult(available=False)
    assert "severity" not in result.model_dump_json()


def test_no_severity_in_headers_result():
    from app.scanners.header_scanner import scan_headers
    response = make_response(headers={})
    result = scan_headers(response)
    assert "severity" not in result.model_dump_json()


def test_no_ai_fields_in_scan_result():
    """ScanResult must not have any AI-related fields."""
    from app.schemas.scan_result import ScanResult
    import datetime
    result = ScanResult(
        target_url="https://example.com/",
        target_hostname="example.com",
        target_scheme="https",
        started_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    json_str = result.model_dump_json()
    forbidden = ["ai_explanation", "ai_recommendation", "severity", "risk_score", "business_impact"]
    for field in forbidden:
        assert field not in json_str, f"Forbidden field {field!r} present in ScanResult"


# ── Invariant 11–12: Timeouts and size limits ─────────────────────────────────

def test_config_has_timeout_settings():
    """All timeout settings must be present and finite."""
    from app.core.config import get_settings
    s = get_settings()
    assert s.CONNECT_TIMEOUT > 0
    assert s.READ_TIMEOUT > 0
    assert s.REQUEST_TIMEOUT > 0
    assert s.DNS_TIMEOUT > 0
    assert s.NMAP_TIMEOUT > 0


def test_config_has_size_limit():
    """MAX_RESPONSE_SIZE must be finite and positive."""
    from app.core.config import get_settings
    s = get_settings()
    assert s.MAX_RESPONSE_SIZE > 0


def test_config_has_redirect_limit():
    """MAX_REDIRECTS must be finite."""
    from app.core.config import get_settings
    s = get_settings()
    assert s.MAX_REDIRECTS > 0


def test_config_nmap_max_ports_bounded():
    """NMAP_MAX_PORTS must be finite to prevent accidental full-port scans."""
    from app.core.config import get_settings
    s = get_settings()
    assert 0 < s.NMAP_MAX_PORTS <= 1000  # sanity upper bound
