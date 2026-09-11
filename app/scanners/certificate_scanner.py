"""
Certificate Scanner — Phase 04.

Extracts raw certificate metadata from an HTTPS connection.

Uses:
  - Python stdlib ssl (for DER/PEM retrieval)
  - cryptography library (for structured certificate parsing)

SECURITY RULES:
  - Private key material is NEVER collected
  - Cookie values, auth headers, credentials are NOT handled here
  - Only observable public certificate metadata is extracted
  - Data minimization: only fields needed for security analysis

What this module does NOT do:
  - Assign severity (Phase 05)
  - Calculate risk score
  - Make trust decisions beyond factual observation
"""

import datetime
import logging
import socket
import ssl
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import (
    ec,
    rsa,
    dsa,
)

from app.schemas.scan_result import (
    CertHostnameState,
    CertValidityState,
    CertificateResult,
    ScannerError,
    ScannerErrorCode,
)
from app.security.target_validator import ValidatedTarget

logger = logging.getLogger(__name__)


def scan_certificate(
    target: ValidatedTarget,
    connect_timeout: float = 5.0,
    now: datetime.datetime | None = None,
) -> CertificateResult:
    """
    Retrieve and parse TLS certificate metadata for an HTTPS target.

    Parameters
    ----------
    target : ValidatedTarget
        Phase 03 validated target.
    connect_timeout : float
        Socket + TLS handshake timeout in seconds.
    now : datetime.datetime, optional
        UTC-aware current time (injectable for deterministic tests).
        Defaults to datetime.datetime.now(tz=datetime.timezone.utc).

    Returns
    -------
    CertificateResult
        Raw certificate observations. Never raises.
    """
    if target.scheme != "https":
        return CertificateResult(available=False)

    if now is None:
        now = datetime.datetime.now(tz=datetime.timezone.utc)

    logger.info("Certificate scan: hostname=%r ip=%r", target.hostname, target.selected_address)

    # ── Retrieve DER certificate ───────────────────────────────────────────────
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # we collect data even for invalid certs

        with socket.create_connection(
            (target.selected_address, target.port),
            timeout=connect_timeout,
        ) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=target.hostname) as tls_sock:
                der_cert = tls_sock.getpeercert(binary_form=True)
                # Also collect chain where available
                _peer_cert_dict = tls_sock.getpeercert()  # for hostname check

    except TimeoutError:
        return CertificateResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.TIMEOUT,
                message="Certificate retrieval timed out.",
            ),
        )
    except (ssl.SSLError, OSError) as exc:
        return CertificateResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.TLS_ERROR,
                message="Could not retrieve certificate.",
            ),
        )

    if not der_cert:
        return CertificateResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.CERTIFICATE_ERROR,
                message="No certificate returned by the server.",
            ),
        )

    # ── Parse with cryptography library ───────────────────────────────────────
    try:
        cert = x509.load_der_x509_certificate(der_cert)
    except Exception:
        return CertificateResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.CERTIFICATE_ERROR,
                message="Certificate could not be parsed.",
            ),
        )

    # ── Extract metadata ──────────────────────────────────────────────────────
    subject = _parse_name(cert.subject)
    issuer  = _parse_name(cert.issuer)

    # Validity
    valid_from  = _ensure_utc(cert.not_valid_before_utc)
    valid_until = _ensure_utc(cert.not_valid_after_utc)
    validity_state, is_expired, days_until_expiry = _classify_validity(
        valid_from, valid_until, now
    )

    # SAN entries
    san_entries = _extract_san(cert)

    # Signature + key info
    sig_algorithm = _safe_attr(cert, "signature_algorithm_oid", "dotted_string")
    try:
        sig_algorithm = cert.signature_hash_algorithm.name if cert.signature_hash_algorithm else None
    except Exception:
        sig_algorithm = None

    pub_key_algo, pub_key_size = _extract_key_info(cert)

    # Hostname validation (using stdlib ssl match logic)
    hostname_state = _check_hostname(target.hostname, _peer_cert_dict)

    # Self-signed detection: issuer == subject
    is_self_signed = subject == issuer

    # Serial number (safe to include — public info)
    serial_number = str(cert.serial_number)

    result = CertificateResult(
        available=True,
        subject=subject,
        issuer=issuer,
        serial_number=serial_number,
        valid_from=valid_from,
        valid_until=valid_until,
        san_entries=san_entries,
        signature_algorithm=sig_algorithm,
        public_key_algorithm=pub_key_algo,
        public_key_size=pub_key_size,
        validity_state=validity_state,
        is_expired=is_expired,
        days_until_expiry=days_until_expiry,
        hostname_validation=hostname_state,
        is_self_signed=is_self_signed,
    )

    logger.info(
        "Certificate parsed: subject=%r validity=%s hostname=%s",
        subject, validity_state.value, hostname_state.value,
    )
    return result


# ── Private helpers ────────────────────────────────────────────────────────────

def _parse_name(name: x509.Name) -> dict[str, str]:
    """Extract RFC 4514 name components into a flat dict."""
    result: dict[str, str] = {}
    for attr in name:
        try:
            key = attr.oid._name  # e.g. "commonName"
            result[key] = str(attr.value)
        except Exception:
            pass
    return result


def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """Ensure the datetime is UTC-aware. cryptography 42+ returns tz-aware datetimes."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _classify_validity(
    valid_from: datetime.datetime,
    valid_until: datetime.datetime,
    now: datetime.datetime,
) -> tuple[CertValidityState, bool, int]:
    """
    Classify certificate temporal validity.

    Returns (state, is_expired, days_until_expiry).
    days_until_expiry is negative when expired.
    """
    delta = valid_until - now
    days = delta.days  # negative when expired

    if now < valid_from:
        return CertValidityState.NOT_YET_VALID, False, days
    elif now > valid_until:
        return CertValidityState.EXPIRED, True, days
    else:
        return CertValidityState.VALID, False, days


def _extract_san(cert: x509.Certificate) -> list[str]:
    """Extract Subject Alternative Names."""
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        entries = []
        for value in san_ext.value:
            if isinstance(value, x509.DNSName):
                entries.append(f"DNS:{value.value}")
            elif isinstance(value, x509.IPAddress):
                entries.append(f"IP:{value.value}")
            else:
                entries.append(str(value))
        return sorted(entries)  # deterministic
    except x509.ExtensionNotFound:
        return []
    except Exception:
        return []


def _extract_key_info(cert: x509.Certificate) -> tuple[str | None, int | None]:
    """Return (algorithm_name, key_size_bits) safely."""
    try:
        pub_key = cert.public_key()
        if isinstance(pub_key, rsa.RSAPublicKey):
            return "RSA", pub_key.key_size
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            return "EC", pub_key.key_size
        elif isinstance(pub_key, dsa.DSAPublicKey):
            return "DSA", pub_key.key_size
        else:
            return type(pub_key).__name__, None
    except Exception:
        return None, None


def _check_hostname(hostname: str, peer_cert_dict: dict) -> CertHostnameState:
    """
    Use stdlib ssl.match_hostname for hostname validation.

    ssl.match_hostname is deprecated in 3.12 but still available.
    We use it because it implements RFC 2818 wildcard matching correctly.
    """
    if not peer_cert_dict:
        return CertHostnameState.VALIDATION_UNAVAILABLE
    try:
        ssl.match_hostname(peer_cert_dict, hostname)  # type: ignore[attr-defined]
        return CertHostnameState.MATCH
    except ssl.CertificateError:
        return CertHostnameState.MISMATCH
    except Exception:
        return CertHostnameState.VALIDATION_UNAVAILABLE


def _safe_attr(obj: Any, *attrs: str) -> Any:
    """Safely navigate a chain of attributes."""
    cur = obj
    for attr in attrs:
        try:
            cur = getattr(cur, attr)
        except Exception:
            return None
    return cur
