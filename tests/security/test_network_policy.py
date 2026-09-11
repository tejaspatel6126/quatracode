"""
Network policy tests.
Tests scheme, port, and IP policy enforcement.
No network connections made.
"""

import pytest

from app.security.errors import SecurityCode, TargetSecurityError
from app.security.network_policy import (
    assert_all_addresses_allowed,
    assert_ip_allowed,
    assert_port_allowed,
    assert_scheme_allowed,
)


# ── Scheme policy ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("scheme", ["http", "https", "HTTP", "HTTPS"])
def test_allowed_schemes_pass(scheme):
    assert_scheme_allowed(scheme)  # should not raise


@pytest.mark.parametrize("scheme", [
    "file", "ftp", "gopher", "data", "javascript",
    "ssh", "telnet", "smtp", "ldap", "unknown", "",
])
def test_blocked_schemes_raise(scheme):
    with pytest.raises(TargetSecurityError) as exc:
        assert_scheme_allowed(scheme)
    assert exc.value.code == SecurityCode.UNSUPPORTED_SCHEME


# ── Port policy ───────────────────────────────────────────────────────────────

def test_http_default_port_allowed():
    assert assert_port_allowed("http", None) == 80


def test_https_default_port_allowed():
    assert assert_port_allowed("https", None) == 443


def test_http_explicit_80_allowed():
    assert assert_port_allowed("http", 80) == 80


def test_https_explicit_443_allowed():
    assert assert_port_allowed("https", 443) == 443


@pytest.mark.parametrize("port", [8080, 8443, 3000, 22, 3306, 1337, 0, 65535])
def test_non_standard_ports_blocked(port):
    with pytest.raises(TargetSecurityError) as exc:
        assert_port_allowed("https", port)
    assert exc.value.code == SecurityCode.INVALID_PORT


# ── IP policy ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", ["8.8.8.8", "1.1.1.1"])
def test_public_ips_allowed(addr):
    assert_ip_allowed(addr)  # should not raise


@pytest.mark.parametrize("addr,expected_code", [
    ("127.0.0.1",         SecurityCode.LOOPBACK_BLOCKED),
    ("::1",               SecurityCode.LOOPBACK_BLOCKED),
    ("10.0.0.1",          SecurityCode.PRIVATE_IP_BLOCKED),
    ("192.168.1.1",       SecurityCode.PRIVATE_IP_BLOCKED),
    ("172.16.0.1",        SecurityCode.PRIVATE_IP_BLOCKED),
    ("fc00::1",           SecurityCode.PRIVATE_IP_BLOCKED),
    ("169.254.0.1",       SecurityCode.LINK_LOCAL_BLOCKED),
    ("fe80::1",           SecurityCode.LINK_LOCAL_BLOCKED),
    ("169.254.169.254",   SecurityCode.METADATA_IP_BLOCKED),  # metadata checked first
    ("224.0.0.1",         SecurityCode.MULTICAST_IP_BLOCKED),
    ("::ffff:127.0.0.1",  SecurityCode.LOOPBACK_BLOCKED),
    ("::ffff:10.0.0.1",   SecurityCode.PRIVATE_IP_BLOCKED),
    ("::ffff:192.168.1.1",SecurityCode.PRIVATE_IP_BLOCKED),
    ("::ffff:169.254.169.254", SecurityCode.METADATA_IP_BLOCKED),
])
def test_unsafe_ip_blocked_with_correct_code(addr, expected_code):
    with pytest.raises(TargetSecurityError) as exc:
        assert_ip_allowed(addr)
    assert exc.value.code == expected_code


# ── All-addresses policy ───────────────────────────────────────────────────────

def test_all_public_addresses_pass():
    assert_all_addresses_allowed(("8.8.8.8", "8.8.4.4"))  # should not raise


def test_mixed_public_private_rejected():
    """If ANY address is private, the whole set is rejected."""
    with pytest.raises(TargetSecurityError) as exc:
        assert_all_addresses_allowed(("8.8.8.8", "10.0.0.1"))
    assert exc.value.code == SecurityCode.PRIVATE_IP_BLOCKED


def test_all_private_addresses_rejected():
    with pytest.raises(TargetSecurityError):
        assert_all_addresses_allowed(("10.0.0.1", "192.168.1.1"))


def test_mixed_public_loopback_rejected():
    with pytest.raises(TargetSecurityError) as exc:
        assert_all_addresses_allowed(("8.8.8.8", "127.0.0.1"))
    assert exc.value.code == SecurityCode.LOOPBACK_BLOCKED


def test_empty_addresses_passes():
    """Empty tuple — no addresses to block. DNS resolver handles empty result separately."""
    assert_all_addresses_allowed(())  # no addresses → no error from this function
