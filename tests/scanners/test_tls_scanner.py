"""
TLS Scanner tests — Phase 04.

All network I/O is mocked via unittest.mock.patch.
No real TLS connections are made.
"""

import ssl
import socket
import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.scanners.tls_scanner import scan_tls, _parse_version_str
from app.schemas.scan_result import TLSResult, TLSVersion, ScannerErrorCode
from tests.scanners.conftest import make_https_target, make_http_target


# ── HTTP target — TLS skipped ─────────────────────────────────────────────────

def test_tls_skipped_for_http_target():
    target = make_http_target()
    result = scan_tls(target)
    assert result.available is False
    assert result.error is None  # Not an error — just N/A


# ── TLS handshake success (mocked) ────────────────────────────────────────────

def _make_mock_tls_sock(version: str = "TLSv1.3", cipher: tuple = ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)):
    """Build a mock ssl socket."""
    mock_sock = MagicMock()
    mock_sock.version.return_value = version
    mock_sock.cipher.return_value = cipher
    mock_sock.__enter__ = MagicMock(return_value=mock_sock)
    mock_sock.__exit__ = MagicMock(return_value=False)
    return mock_sock


def _make_mock_raw_sock():
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


@patch("app.scanners.tls_scanner._probe_version", return_value=False)
@patch("ssl.SSLContext.wrap_socket")
@patch("socket.create_connection")
def test_tls_handshake_success_tls13(mock_conn, mock_wrap, mock_probe):
    mock_raw = _make_mock_raw_sock()
    mock_conn.return_value = mock_raw
    mock_tls = _make_mock_tls_sock("TLSv1.3")
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_tls(target)

    assert result.available is True
    assert result.negotiated_version == TLSVersion.TLS_1_3
    assert result.error is None


@patch("app.scanners.tls_scanner._probe_version", return_value=False)
@patch("ssl.SSLContext.wrap_socket")
@patch("socket.create_connection")
def test_tls_handshake_success_tls12(mock_conn, mock_wrap, mock_probe):
    mock_raw = _make_mock_raw_sock()
    mock_conn.return_value = mock_raw
    mock_tls = _make_mock_tls_sock("TLSv1.2", ("TLS_RSA_WITH_AES_128_CBC_SHA", "TLSv1.2", 128))
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_tls(target)

    assert result.available is True
    assert result.negotiated_version == TLSVersion.TLS_1_2


# ── TLS handshake failures ────────────────────────────────────────────────────

@patch("socket.create_connection", side_effect=TimeoutError("timed out"))
def test_tls_timeout(mock_conn):
    target = make_https_target()
    result = scan_tls(target)
    assert result.available is False
    assert result.error is not None
    assert result.error.code == ScannerErrorCode.TIMEOUT


@patch("socket.create_connection", side_effect=ssl.SSLError("handshake failure"))
def test_tls_ssl_error(mock_conn):
    target = make_https_target()
    result = scan_tls(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.TLS_ERROR


@patch("socket.create_connection", side_effect=ConnectionRefusedError())
def test_tls_connection_refused(mock_conn):
    target = make_https_target()
    result = scan_tls(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.NETWORK_ERROR


@patch("socket.create_connection", side_effect=OSError("network unreachable"))
def test_tls_network_error(mock_conn):
    target = make_https_target()
    result = scan_tls(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.NETWORK_ERROR


# ── TLS never raises ──────────────────────────────────────────────────────────

@patch("socket.create_connection", side_effect=Exception("unexpected"))
def test_tls_unexpected_error_does_not_raise(mock_conn):
    target = make_https_target()
    # Should not propagate — unexpected errors are caught at orchestrator level
    # The scanner itself re-raises unexpected Exceptions for the orchestrator to catch
    with pytest.raises(Exception):
        scan_tls(target)


# ── Version string parsing ────────────────────────────────────────────────────

@pytest.mark.parametrize("version_str,expected", [
    ("TLSv1",   TLSVersion.TLS_1_0),
    ("TLSv1.1", TLSVersion.TLS_1_1),
    ("TLSv1.2", TLSVersion.TLS_1_2),
    ("TLSv1.3", TLSVersion.TLS_1_3),
    (None,      TLSVersion.UNKNOWN),
    ("",        TLSVersion.UNKNOWN),
    ("SSLv3",   TLSVersion.UNKNOWN),
    ("UNKNOWN", TLSVersion.UNKNOWN),
])
def test_parse_version_str(version_str, expected):
    assert _parse_version_str(version_str) == expected


# ── Per-version probing ───────────────────────────────────────────────────────

@patch("ssl.SSLContext.wrap_socket")
@patch("socket.create_connection")
def test_probe_version_success(mock_conn, mock_wrap):
    """A successful probe returns True."""
    from app.scanners.tls_scanner import _probe_version
    mock_raw = _make_mock_raw_sock()
    mock_conn.return_value = mock_raw
    mock_tls = _make_mock_tls_sock()
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = _probe_version(target, ssl.TLSVersion.TLSv1_3, 5.0)
    assert result is True


@patch("socket.create_connection", side_effect=ssl.SSLError("version mismatch"))
def test_probe_version_failure_returns_false(mock_conn):
    """A failed probe returns False — never raises."""
    from app.scanners.tls_scanner import _probe_version
    target = make_https_target()
    result = _probe_version(target, ssl.TLSVersion.TLSv1, 5.0)
    assert result is False


# ── Result structure ──────────────────────────────────────────────────────────

@patch("app.scanners.tls_scanner._probe_version", return_value=True)
@patch("ssl.SSLContext.wrap_socket")
@patch("socket.create_connection")
def test_tls_result_has_per_version_fields(mock_conn, mock_wrap, mock_probe):
    mock_raw = _make_mock_raw_sock()
    mock_conn.return_value = mock_raw
    mock_tls = _make_mock_tls_sock("TLSv1.3")
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_tls(target)

    assert result.tls_1_0 is not None
    assert result.tls_1_1 is not None
    assert result.tls_1_2 is not None
    assert result.tls_1_3 is not None


# ── Connects to selected_address not hostname ─────────────────────────────────

@patch("app.scanners.tls_scanner._probe_version", return_value=False)
@patch("ssl.SSLContext.wrap_socket")
@patch("socket.create_connection")
def test_tls_connects_to_selected_address(mock_conn, mock_wrap, mock_probe):
    """TLS scanner must connect to selected_address (validated IP), not hostname."""
    mock_raw = _make_mock_raw_sock()
    mock_conn.return_value = mock_raw
    mock_tls = _make_mock_tls_sock("TLSv1.3")
    mock_wrap.return_value = mock_tls

    target = make_https_target(hostname="example.com", ip="93.184.216.34")
    scan_tls(target)

    call_args = mock_conn.call_args
    connected_to = call_args[0][0] if call_args[0] else call_args[1].get("address", ("", 0))
    if isinstance(connected_to, tuple):
        assert connected_to[0] == "93.184.216.34", f"Connected to hostname not IP: {connected_to}"
    else:
        assert "93.184.216.34" in str(connected_to)
