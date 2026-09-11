"""
Certificate Scanner tests — Phase 04.

All TLS connections are mocked. No real certificates used.
Controlled datetime injection for expiry tests.
"""

import datetime
import ssl
from unittest.mock import MagicMock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.scanners.certificate_scanner import scan_certificate, _classify_validity
from app.schemas.scan_result import (
    CertHostnameState,
    CertValidityState,
    CertificateResult,
    ScannerErrorCode,
)
from tests.scanners.conftest import make_https_target, make_http_target, UTC


# ── Helpers: generate test certificates ───────────────────────────────────────

def _make_cert(
    hostname: str = "example.com",
    valid_from: datetime.datetime | None = None,
    valid_until: datetime.datetime | None = None,
    self_signed: bool = False,
    add_san: bool = True,
) -> tuple[x509.Certificate, bytes]:
    """
    Generate a minimal self-signed certificate for testing.
    Returns (cert_object, der_bytes).
    """
    now = datetime.datetime.now(tz=UTC)
    if valid_from is None:
        valid_from = now - datetime.timedelta(days=1)
    if valid_until is None:
        valid_until = now + datetime.timedelta(days=90)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject_name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
    ])
    issuer_name = subject_name if self_signed else x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Test CA"),
    ])

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject_name)
        .issuer_name(issuer_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
    )

    if add_san:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )

    cert = builder.sign(key, hashes.SHA256())
    der = cert.public_bytes(serialization.Encoding.DER)
    return cert, der


def _patch_tls_for_cert(der: bytes, peer_dict: dict | None = None):
    """Context manager that patches socket + ssl to return a controlled cert."""
    mock_raw = MagicMock()
    mock_raw.__enter__ = MagicMock(return_value=mock_raw)
    mock_raw.__exit__ = MagicMock(return_value=False)

    mock_tls = MagicMock()
    mock_tls.getpeercert.side_effect = lambda binary_form=False: der if binary_form else (peer_dict or {})
    mock_tls.__enter__ = MagicMock(return_value=mock_tls)
    mock_tls.__exit__ = MagicMock(return_value=False)

    return mock_raw, mock_tls


# ── HTTP target — cert skipped ────────────────────────────────────────────────

def test_cert_skipped_for_http():
    target = make_http_target()
    result = scan_certificate(target)
    assert result.available is False
    assert result.error is None


# ── Valid certificate ─────────────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_valid_certificate_parsed(mock_wrap, mock_conn):
    _, der = _make_cert("example.com")
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    now = datetime.datetime.now(tz=UTC)
    result = scan_certificate(target, now=now)

    assert result.available is True
    assert result.validity_state == CertValidityState.VALID
    assert result.is_expired is False
    assert result.days_until_expiry is not None
    assert result.days_until_expiry > 0
    assert result.error is None


# ── Expired certificate ───────────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_expired_certificate_detected(mock_wrap, mock_conn):
    now = datetime.datetime.now(tz=UTC)
    valid_from  = now - datetime.timedelta(days=400)
    valid_until = now - datetime.timedelta(days=10)

    _, der = _make_cert("example.com", valid_from=valid_from, valid_until=valid_until)
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target, now=now)

    assert result.available is True
    assert result.validity_state == CertValidityState.EXPIRED
    assert result.is_expired is True
    assert result.days_until_expiry is not None
    assert result.days_until_expiry < 0


# ── Not-yet-valid certificate ──────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_not_yet_valid_certificate_detected(mock_wrap, mock_conn):
    now = datetime.datetime.now(tz=UTC)
    valid_from  = now + datetime.timedelta(days=5)
    valid_until = now + datetime.timedelta(days=365)

    _, der = _make_cert("example.com", valid_from=valid_from, valid_until=valid_until)
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target, now=now)

    assert result.validity_state == CertValidityState.NOT_YET_VALID


def test_not_yet_valid_certificate_detected_simple():
    """Unit test for _classify_validity without network."""
    now = datetime.datetime(2024, 1, 15, tzinfo=UTC)
    valid_from  = datetime.datetime(2024, 1, 20, tzinfo=UTC)
    valid_until = datetime.datetime(2025, 1, 20, tzinfo=UTC)

    state, is_expired, days = _classify_validity(valid_from, valid_until, now)
    assert state == CertValidityState.NOT_YET_VALID
    assert is_expired is False


# ── Self-signed detection ──────────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_self_signed_detected(mock_wrap, mock_conn):
    _, der = _make_cert("example.com", self_signed=True)
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target)

    assert result.available is True
    assert result.is_self_signed is True


# ── SAN extraction ────────────────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_san_entries_extracted(mock_wrap, mock_conn):
    _, der = _make_cert("example.com", add_san=True)
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target)

    assert result.available is True
    assert len(result.san_entries) > 0
    assert any("example.com" in e for e in result.san_entries)


# ── Certificate timeout ───────────────────────────────────────────────────────

@patch("socket.create_connection", side_effect=TimeoutError())
def test_cert_timeout_structured(mock_conn):
    target = make_https_target()
    result = scan_certificate(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.TIMEOUT


# ── SSL error ─────────────────────────────────────────────────────────────────

@patch("socket.create_connection", side_effect=ssl.SSLError("cert invalid"))
def test_cert_ssl_error_structured(mock_conn):
    target = make_https_target()
    result = scan_certificate(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.TLS_ERROR


# ── No cert returned ──────────────────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_no_cert_returned(mock_wrap, mock_conn):
    mock_raw = MagicMock()
    mock_raw.__enter__ = MagicMock(return_value=mock_raw)
    mock_raw.__exit__ = MagicMock(return_value=False)

    mock_tls = MagicMock()
    mock_tls.getpeercert.return_value = None
    mock_tls.__enter__ = MagicMock(return_value=mock_tls)
    mock_tls.__exit__ = MagicMock(return_value=False)

    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target)
    assert result.available is False
    assert result.error.code == ScannerErrorCode.CERTIFICATE_ERROR


# ── Private key never collected ───────────────────────────────────────────────

@patch("socket.create_connection")
@patch("ssl.SSLContext.wrap_socket")
def test_private_key_never_in_result(mock_wrap, mock_conn):
    _, der = _make_cert("example.com")
    mock_raw, mock_tls = _patch_tls_for_cert(der)
    mock_conn.return_value = mock_raw
    mock_wrap.return_value = mock_tls

    target = make_https_target()
    result = scan_certificate(target)

    result_json = result.model_dump_json()
    assert "PRIVATE KEY" not in result_json
    assert "private_key" not in result_json.lower()
    # No severity in the result
    assert "severity" not in result_json.lower()


# ── Classify validity unit tests ──────────────────────────────────────────────

def test_classify_validity_valid():
    now   = datetime.datetime(2024, 6, 15, tzinfo=UTC)
    start = datetime.datetime(2024, 1, 1, tzinfo=UTC)
    end   = datetime.datetime(2025, 1, 1, tzinfo=UTC)
    state, expired, days = _classify_validity(start, end, now)
    assert state == CertValidityState.VALID
    assert expired is False
    assert days > 0


def test_classify_validity_expired():
    now   = datetime.datetime(2025, 6, 15, tzinfo=UTC)
    start = datetime.datetime(2024, 1, 1, tzinfo=UTC)
    end   = datetime.datetime(2025, 1, 1, tzinfo=UTC)
    state, expired, days = _classify_validity(start, end, now)
    assert state == CertValidityState.EXPIRED
    assert expired is True
    assert days < 0


def test_classify_validity_days_until_expiry_deterministic():
    """Days calculation must be deterministic given fixed clock."""
    now   = datetime.datetime(2024, 6, 15, tzinfo=UTC)
    start = datetime.datetime(2024, 1, 1, tzinfo=UTC)
    end   = datetime.datetime(2024, 9, 15, tzinfo=UTC)  # 92 days from now
    _, _, days = _classify_validity(start, end, now)
    assert days == 92
