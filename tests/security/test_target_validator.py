"""
Target validator tests — Phase 03 core security boundary.

All DNS resolution is mocked. No real network connections are made.

Coverage:
  - Valid URLs
  - Invalid schemes (file, ftp, gopher, data, javascript, ssh, telnet)
  - Missing scheme / hostname
  - URL credentials (rejected)
  - Port policy
  - Hostname validation
  - Control characters / extreme inputs
  - DNS failure / empty / timeout
  - Private IP blocking (all categories)
  - IPv4-mapped IPv6 blocking
  - DNS rebinding protection
  - Multiple DNS records (public+private → rejected)
  - Validated target structure
"""

import pytest
from unittest.mock import patch

from app.security.dns_resolver import DNSResult
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.target_validator import ValidatedTarget, validate_target


# ── Mock resolver helpers ──────────────────────────────────────────────────────

def _resolver_public(hostname, timeout=5.0):
    """Always resolves to a public IP."""
    return DNSResult(hostname=hostname, addresses=("93.184.216.34",), success=True)


def _resolver_private(hostname, timeout=5.0):
    """Always resolves to a private IP."""
    return DNSResult(hostname=hostname, addresses=("10.0.0.1",), success=True)


def _resolver_loopback(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("127.0.0.1",), success=True)


def _resolver_link_local(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("169.254.1.1",), success=True)


def _resolver_metadata(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("169.254.169.254",), success=True)


def _resolver_ipv6_loopback(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("::1",), success=True)


def _resolver_ipv4_mapped_loopback(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("::ffff:127.0.0.1",), success=True)


def _resolver_ipv4_mapped_private(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("::ffff:10.0.0.1",), success=True)


def _resolver_ipv4_mapped_metadata(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=("::ffff:169.254.169.254",), success=True)


def _resolver_dns_failure(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=(), success=False, error="Name not found")


def _resolver_dns_timeout(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=(), success=False, error="DNS timeout")


def _resolver_empty(hostname, timeout=5.0):
    return DNSResult(hostname=hostname, addresses=(), success=True)


def _resolver_mixed_public_private(hostname, timeout=5.0):
    """Public + private in same result — should be rejected."""
    return DNSResult(hostname=hostname, addresses=("8.8.8.8", "10.0.0.1"), success=True)


def _resolver_multiple_public(hostname, timeout=5.0):
    """Multiple public IPs — allowed."""
    return DNSResult(hostname=hostname, addresses=("8.8.8.8", "8.8.4.4"), success=True)


# ── Valid URLs ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://example.com",
    "http://example.com",
    "https://example.com/",
    "https://example.com/path",
    "https://example.com/path?q=1",
    "  https://example.com  ",  # whitespace stripped
    "HTTPS://EXAMPLE.COM",      # case normalized
])
def test_valid_urls_pass(url):
    result = validate_target(url, resolver=_resolver_public)
    assert isinstance(result, ValidatedTarget)
    assert result.scheme in ("http", "https")
    assert result.hostname == "example.com"


def test_validated_target_has_selected_address():
    result = validate_target("https://example.com", resolver=_resolver_public)
    assert result.selected_address == "93.184.216.34"


def test_validated_target_stores_all_addresses():
    result = validate_target("https://example.com", resolver=_resolver_multiple_public)
    assert "8.8.8.8" in result.dns_result.addresses
    assert "8.8.4.4" in result.dns_result.addresses


def test_validated_target_is_frozen():
    result = validate_target("https://example.com", resolver=_resolver_public)
    with pytest.raises((AttributeError, TypeError)):
        result.hostname = "evil.com"  # type: ignore[misc]


def test_normalized_url_lowercase():
    result = validate_target("HTTPS://EXAMPLE.COM/PATH", resolver=_resolver_public)
    assert result.scheme == "https"
    assert result.hostname == "example.com"


# ── Scheme validation ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "file://localhost/etc/shadow",
    "ftp://example.com",
    "gopher://example.com",
    "data:text/html,<h1>test</h1>",
    "javascript:alert(1)",
    "ssh://example.com",
    "telnet://example.com",
    "smtp://example.com",
    "ldap://example.com",
    "unknown://example.com",
    "custom://example.com",
])
def test_blocked_schemes_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.UNSUPPORTED_SCHEME


# ── Missing scheme / hostname ─────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "example.com",          # no scheme
    "//example.com",        # scheme-relative
    "",                     # empty
    "   ",                  # whitespace only
])
def test_missing_scheme_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.INVALID_URL


def test_missing_hostname_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://", resolver=_resolver_public)
    assert exc.value.code == SecurityCode.INVALID_HOSTNAME


# ── URL credentials ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://user@example.com",
    "https://user:password@example.com",
    "https://admin:secret@example.com/path",
    "http://root:toor@192.168.1.1",
])
def test_url_credentials_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.URL_CREDENTIALS_NOT_ALLOWED


def test_credentials_not_in_error_message():
    """Credentials (passwords) must NEVER appear in error messages."""
    url = "https://user:s3cr3tP4ss@example.com"
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    # The secret password must never appear in the error message
    assert "s3cr3tP4ss" not in exc.value.message
    # The code must be the credential error
    assert exc.value.code == SecurityCode.URL_CREDENTIALS_NOT_ALLOWED


# ── Port policy ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://example.com:443",
    "http://example.com:80",
])
def test_standard_ports_accepted(url):
    result = validate_target(url, resolver=_resolver_public)
    assert isinstance(result, ValidatedTarget)


@pytest.mark.parametrize("url", [
    "https://example.com:8080",
    "https://example.com:8443",
    "http://example.com:3000",
    "https://example.com:22",
    "https://example.com:3306",
])
def test_nonstandard_ports_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.INVALID_PORT


# ── Hostname validation ───────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://" + "a" * 254 + ".com",  # too long
])
def test_excessively_long_hostname_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.INVALID_HOSTNAME


def test_hostname_with_invalid_chars_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://ex ample.com", resolver=_resolver_public)
    # Could be INVALID_HOSTNAME or INVALID_URL depending on urlparse behavior
    assert exc.value.code in (SecurityCode.INVALID_HOSTNAME, SecurityCode.INVALID_URL)


# ── Control characters ────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://example.com\x00/evil",  # null byte
    "https://example.com\r\nX-Injected: header",  # CRLF injection
    "https://example.com\x01",
    "https://\x00evil.com",
])
def test_control_characters_rejected(url):
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code in (
        SecurityCode.INVALID_URL,
        SecurityCode.INVALID_HOSTNAME,
        SecurityCode.UNSUPPORTED_SCHEME,
    )


def test_url_too_long_rejected():
    url = "https://example.com/" + "a" * 2100
    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=_resolver_public)
    assert exc.value.code == SecurityCode.INVALID_URL


# ── DNS failure / empty / timeout ─────────────────────────────────────────────

def test_dns_failure_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_dns_failure)
    assert exc.value.code == SecurityCode.DNS_RESOLUTION_FAILED


def test_dns_timeout_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_dns_timeout)
    assert exc.value.code == SecurityCode.DNS_TIMEOUT


def test_dns_empty_result_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_empty)
    assert exc.value.code == SecurityCode.DNS_EMPTY_RESULT


# ── IP security (all categories) ──────────────────────────────────────────────

def test_private_ip_blocked():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://internal.example.com", resolver=_resolver_private)
    assert exc.value.code == SecurityCode.PRIVATE_IP_BLOCKED


def test_loopback_blocked():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_loopback)
    assert exc.value.code == SecurityCode.LOOPBACK_BLOCKED


def test_link_local_blocked():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_link_local)
    assert exc.value.code == SecurityCode.LINK_LOCAL_BLOCKED


def test_metadata_ip_blocked():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_metadata)
    assert exc.value.code == SecurityCode.METADATA_IP_BLOCKED


def test_ipv6_loopback_blocked():
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_ipv6_loopback)
    assert exc.value.code == SecurityCode.LOOPBACK_BLOCKED


# ── IPv4-mapped IPv6 ───────────────────────────────────────────────────────────

def test_ipv4_mapped_loopback_blocked():
    """::ffff:127.0.0.1 must be blocked as loopback."""
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_ipv4_mapped_loopback)
    assert exc.value.code == SecurityCode.LOOPBACK_BLOCKED


def test_ipv4_mapped_private_blocked():
    """::ffff:10.0.0.1 must be blocked as private."""
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_ipv4_mapped_private)
    assert exc.value.code == SecurityCode.PRIVATE_IP_BLOCKED


def test_ipv4_mapped_metadata_blocked():
    """::ffff:169.254.169.254 must be blocked as metadata."""
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_ipv4_mapped_metadata)
    assert exc.value.code == SecurityCode.METADATA_IP_BLOCKED


# ── DNS rebinding protection ───────────────────────────────────────────────────

def test_dns_rebinding_selected_address_pinned():
    """
    The ValidatedTarget stores selected_address.
    The Safe HTTP Client must use this address instead of re-resolving.
    Simulates: first resolution → public IP (passes validation).
    Second resolution (after validation) → private IP.
    The selected_address must remain the validated public IP.
    """
    call_count = {"n": 0}

    def rebinding_resolver(hostname, timeout=5.0):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # First call: public IP — passes validation
            return DNSResult(hostname=hostname, addresses=("8.8.8.8",), success=True)
        else:
            # Subsequent calls: private IP — but validator won't be called again
            return DNSResult(hostname=hostname, addresses=("10.0.0.1",), success=True)

    result = validate_target("https://example.com", resolver=rebinding_resolver)
    # selected_address is from the first (validated) resolution
    assert result.selected_address == "8.8.8.8"
    # The Safe HTTP Client will connect to 8.8.8.8, not re-resolve


def test_dns_rebinding_scenario_private_second_call_cannot_bypass():
    """If DNS rebinding gives private IP on first call, it is rejected."""
    result_holder = {"calls": 0}

    def rebinding_private_resolver(hostname, timeout=5.0):
        result_holder["calls"] += 1
        if result_holder["calls"] == 1:
            return DNSResult(hostname=hostname, addresses=("10.0.0.1",), success=True)
        return DNSResult(hostname=hostname, addresses=("8.8.8.8",), success=True)

    # First call is private → must be rejected
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=rebinding_private_resolver)
    assert exc.value.code == SecurityCode.PRIVATE_IP_BLOCKED


# ── Multiple DNS records ──────────────────────────────────────────────────────

def test_multiple_public_ips_allowed():
    result = validate_target("https://example.com", resolver=_resolver_multiple_public)
    assert isinstance(result, ValidatedTarget)


def test_mixed_public_and_private_rejected():
    """One private IP in a mixed result must reject the entire target."""
    with pytest.raises(TargetSecurityError) as exc:
        validate_target("https://example.com", resolver=_resolver_mixed_public_private)
    assert exc.value.code == SecurityCode.PRIVATE_IP_BLOCKED


# ── Invariant checks ──────────────────────────────────────────────────────────

def test_raw_url_never_in_validated_target():
    """The validated target must not expose the raw (user-provided) URL directly."""
    raw = "  HTTPS://EXAMPLE.COM/path?q=1  "
    result = validate_target(raw, resolver=_resolver_public)
    # normalized_url should not have leading/trailing whitespace
    assert result.normalized_url == result.normalized_url.strip()
    assert "  " not in result.normalized_url


@pytest.mark.parametrize("url", [
    "https://user:hunter2@example.com",
    "https://admin@example.com",
])
def test_credentials_never_reach_dns(url):
    """DNS resolver must never be called with a credential-bearing URL."""
    resolver_called_with = []

    def recording_resolver(hostname, timeout=5.0):
        resolver_called_with.append(hostname)
        return DNSResult(hostname=hostname, addresses=(), success=False)

    with pytest.raises(TargetSecurityError) as exc:
        validate_target(url, resolver=recording_resolver)
    assert exc.value.code == SecurityCode.URL_CREDENTIALS_NOT_ALLOWED
    # DNS was never called (credentials rejected before DNS step)
    assert len(resolver_called_with) == 0
