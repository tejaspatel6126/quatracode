"""
DNS resolver tests.
Uses mocked socket calls — no real DNS queries made.
"""

import socket
from unittest.mock import patch, MagicMock

import pytest

from app.security.dns_resolver import DNSResult, resolve_hostname


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mock_getaddrinfo(results: list[tuple]):
    """
    Returns a mock for socket.getaddrinfo.
    results: list of (family, type, proto, canonname, sockaddr) tuples.
    """
    return MagicMock(return_value=results)


def _addr_entry(ip: str, port: int = 0, family=socket.AF_INET):
    """Build a fake getaddrinfo entry."""
    sockaddr = (ip, port) if family == socket.AF_INET else (ip, port, 0, 0)
    return (family, socket.SOCK_STREAM, 6, "", sockaddr)


# ── Basic resolution ──────────────────────────────────────────────────────────

def test_resolve_public_ipv4():
    entries = [_addr_entry("93.184.216.34")]
    with patch("socket.getaddrinfo", _mock_getaddrinfo(entries)):
        result = resolve_hostname("example.com")
    assert result.success is True
    assert "93.184.216.34" in result.addresses
    assert result.error is None


def test_resolve_multiple_addresses():
    entries = [
        _addr_entry("8.8.8.8"),
        _addr_entry("8.8.4.4"),
    ]
    with patch("socket.getaddrinfo", _mock_getaddrinfo(entries)):
        result = resolve_hostname("dns.google")
    assert result.success is True
    assert len(result.addresses) == 2


def test_resolve_deduplicates_addresses():
    # Same IP returned twice (can happen in practice)
    entries = [
        _addr_entry("8.8.8.8"),
        _addr_entry("8.8.8.8"),
    ]
    with patch("socket.getaddrinfo", _mock_getaddrinfo(entries)):
        result = resolve_hostname("dns.google")
    assert result.addresses.count("8.8.8.8") == 1


def test_resolve_ipv6_address():
    entries = [
        (_addr_entry.__code__.co_freevars, None, None, None,
         ("2606:2800:220:1:248:1893:25c8:1946", 0, 0, 0)),
    ]
    # Use a simpler mock
    mock_result = [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "",
         ("2606:2800:220:1:248:1893:25c8:1946", 0, 0, 0)),
    ]
    with patch("socket.getaddrinfo", return_value=mock_result):
        result = resolve_hostname("example.com")
    assert result.success is True
    assert "2606:2800:220:1:248:1893:25c8:1946" in result.addresses


# ── Empty hostname ────────────────────────────────────────────────────────────

def test_resolve_empty_hostname():
    result = resolve_hostname("")
    assert result.success is False
    assert result.addresses == ()


# ── DNS failure ───────────────────────────────────────────────────────────────

def test_resolve_dns_failure():
    with patch("socket.getaddrinfo", side_effect=socket.gaierror("Name not found")):
        result = resolve_hostname("nonexistent.invalid")
    assert result.success is False
    assert result.addresses == ()
    assert result.error is not None


# ── DNS timeout ───────────────────────────────────────────────────────────────

def test_resolve_dns_timeout():
    with patch("socket.getaddrinfo", side_effect=TimeoutError("timed out")):
        result = resolve_hostname("slow.example.com", timeout=1.0)
    assert result.success is False
    assert "timeout" in (result.error or "").lower()


# ── Empty result ──────────────────────────────────────────────────────────────

def test_resolve_empty_result():
    with patch("socket.getaddrinfo", return_value=[]):
        result = resolve_hostname("empty.example.com")
    assert result.success is True
    assert result.is_empty is True
    assert result.addresses == ()


# ── Result structure ──────────────────────────────────────────────────────────

def test_dns_result_is_frozen():
    result = DNSResult(hostname="example.com", addresses=("8.8.8.8",), success=True)
    with pytest.raises((AttributeError, TypeError)):
        result.success = False  # type: ignore[misc]


def test_dns_result_not_empty_when_has_addresses():
    result = DNSResult(hostname="example.com", addresses=("8.8.8.8",), success=True)
    assert result.is_empty is False
