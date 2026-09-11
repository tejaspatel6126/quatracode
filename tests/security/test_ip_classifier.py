"""
IP classifier tests.
Tests every IPv4/IPv6 address category using proper ipaddress classification.
No network connections made.
"""

import pytest

from app.security.ip_classifier import (
    IPCategory,
    classify_ip,
    is_metadata_address,
    is_safe_for_scanning,
)


# ── Loopback ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "127.0.0.1",
    "127.0.0.2",
    "127.255.255.255",
    "::1",
])
def test_loopback_classified(addr):
    assert classify_ip(addr) == IPCategory.LOOPBACK


# ── Private (RFC 1918) ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "10.0.0.1",
    "10.255.255.255",
    "172.16.0.1",
    "172.31.255.255",
    "192.168.0.1",
    "192.168.255.255",
])
def test_private_ipv4_classified(addr):
    assert classify_ip(addr) == IPCategory.PRIVATE


@pytest.mark.parametrize("addr", [
    "fc00::1",
    "fd00::1",
    "fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
])
def test_private_ipv6_classified(addr):
    assert classify_ip(addr) == IPCategory.PRIVATE


# ── Link-local ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "169.254.0.1",
    "169.254.100.100",
    "169.254.255.255",
    "fe80::1",
    "fe80::abcd:1234",
])
def test_link_local_classified(addr):
    assert classify_ip(addr) == IPCategory.LINK_LOCAL


# ── Cloud metadata (link-local but explicitly checked) ────────────────────────

def test_metadata_address_169_254_169_254():
    assert classify_ip("169.254.169.254") == IPCategory.LINK_LOCAL
    assert is_metadata_address("169.254.169.254") is True


def test_metadata_check_non_metadata():
    assert is_metadata_address("8.8.8.8") is False
    assert is_metadata_address("169.254.1.1") is False


# ── Multicast ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "224.0.0.1",
    "239.255.255.255",
    "ff02::1",
    "ff00::1",
])
def test_multicast_classified(addr):
    assert classify_ip(addr) == IPCategory.MULTICAST


# ── Unspecified ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "0.0.0.0",
    "::",
])
def test_unspecified_classified(addr):
    assert classify_ip(addr) == IPCategory.UNSPECIFIED


# ── Public ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "8.8.8.8",
    "8.8.4.4",
    "1.1.1.1",
    "93.184.216.34",   # example.com
    "2606:2800:220:1:248:1893:25c8:1946",  # example.com IPv6
])
def test_public_classified(addr):
    assert classify_ip(addr) == IPCategory.PUBLIC


# ── IPv4-mapped IPv6 ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("mapped,expected_category", [
    ("::ffff:127.0.0.1",   IPCategory.LOOPBACK),
    ("::ffff:10.0.0.1",    IPCategory.PRIVATE),
    ("::ffff:192.168.1.1", IPCategory.PRIVATE),
    ("::ffff:172.16.0.1",  IPCategory.PRIVATE),
    ("::ffff:169.254.1.1", IPCategory.LINK_LOCAL),
    ("::ffff:169.254.169.254", IPCategory.LINK_LOCAL),
    ("::ffff:8.8.8.8",    IPCategory.PUBLIC),
])
def test_ipv4_mapped_ipv6_unwrapped(mapped, expected_category):
    """IPv4-mapped IPv6 must be classified as the underlying IPv4."""
    assert classify_ip(mapped) == expected_category


def test_ipv4_mapped_loopback_not_public():
    """::ffff:127.0.0.1 must NOT be classified as PUBLIC."""
    assert classify_ip("::ffff:127.0.0.1") != IPCategory.PUBLIC


def test_ipv4_mapped_metadata_detected():
    assert is_metadata_address("::ffff:169.254.169.254") is True


# ── is_safe_for_scanning ──────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "127.0.0.1",
    "10.0.0.1",
    "192.168.1.1",
    "172.16.0.1",
    "169.254.169.254",
    "::1",
    "fc00::1",
    "::ffff:127.0.0.1",
    "::ffff:10.0.0.1",
])
def test_unsafe_addresses_not_safe_for_scanning(addr):
    assert is_safe_for_scanning(addr) is False


@pytest.mark.parametrize("addr", [
    "8.8.8.8",
    "1.1.1.1",
])
def test_public_addresses_safe_for_scanning(addr):
    assert is_safe_for_scanning(addr) is True


def test_invalid_ip_not_safe_for_scanning():
    assert is_safe_for_scanning("not-an-ip") is False


def test_invalid_ip_raises_valueerror():
    with pytest.raises(ValueError):
        classify_ip("not-an-ip")
