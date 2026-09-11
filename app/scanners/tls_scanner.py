"""
TLS Scanner — Phase 04.

Inspects TLS availability, negotiated protocol version, and handshake
success using Python's stdlib ssl module.

SECURITY RULE: Only the pre-validated IP from ValidatedTarget is used
for socket connections — no hostname-based DNS re-resolution.

What this module does:
  - Attempt a TLS handshake to the validated IP + port
  - Extract the negotiated protocol version
  - Attempt per-version probing (TLS 1.0/1.1/1.2/1.3) via ssl.SSLContext
  - Return TLSResult (raw observations — no severity)

What this module does NOT do:
  - Assign severity
  - Calculate risk
  - Parse certificates (that is CertificateScanner's job)
"""

import logging
import socket
import ssl

from app.schemas.scan_result import (
    ScannerError,
    ScannerErrorCode,
    TLSResult,
    TLSVersion,
)
from app.security.target_validator import ValidatedTarget

logger = logging.getLogger(__name__)

# TLS protocol constants
_PROTOCOL_VERSION_MAP: dict[int, TLSVersion] = {
    # ssl.TLSVersion enum values (Python 3.7+)
    770: TLSVersion.TLS_1_0,    # ssl.TLSVersion.TLSv1
    771: TLSVersion.TLS_1_1,    # ssl.TLSVersion.TLSv1_1
    772: TLSVersion.TLS_1_2,    # ssl.TLSVersion.TLSv1_2
    773: TLSVersion.TLS_1_3,    # ssl.TLSVersion.TLSv1_3
}

# Deprecated versions per SCANNER_SPECIFICATION.md §14
_DEPRECATED_VERSIONS: frozenset[TLSVersion] = frozenset({
    TLSVersion.TLS_1_0,
    TLSVersion.TLS_1_1,
})


def scan_tls(target: ValidatedTarget, connect_timeout: float = 5.0) -> TLSResult:
    """
    Perform TLS inspection for an HTTPS target.

    For HTTP targets, returns TLSResult(available=False) immediately.

    Connects to target.selected_address (the pre-validated IP) with
    the hostname as SNI, so TLS certificate validation uses the right
    hostname while the TCP connection goes to the known-safe IP.

    Parameters
    ----------
    target : ValidatedTarget
        Phase 03 validated target (scheme, hostname, port, selected_address).
    connect_timeout : float
        TCP + TLS handshake timeout in seconds.

    Returns
    -------
    TLSResult
        Raw TLS observations. Never raises — errors are structured.
    """
    if target.scheme != "https":
        logger.debug("TLS scan skipped: scheme=%r (not HTTPS)", target.scheme)
        return TLSResult(available=False)

    logger.info("TLS scan: hostname=%r ip=%r port=%d",
                target.hostname, target.selected_address, target.port)

    # ── Primary handshake (system default TLS context) ─────────────────────────
    negotiated_version: TLSVersion | None = None
    cipher_suite: str | None = None

    try:
        ctx = ssl.create_default_context()
        # We deliberately set check_hostname=False and verify_mode=CERT_NONE so
        # that the TLS scanner collects factual data about the certificate even
        # for self-signed / expired / mismatched certs. CertificateScanner
        # performs the validity analysis on the raw cert data.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with socket.create_connection(
            (target.selected_address, target.port),
            timeout=connect_timeout,
        ) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=target.hostname) as tls_sock:
                version_str = tls_sock.version()  # e.g. "TLSv1.2", "TLSv1.3"
                cipher_suite = tls_sock.cipher()[0] if tls_sock.cipher() else None
                negotiated_version = _parse_version_str(version_str)

        logger.info("TLS handshake success: version=%r cipher=%r",
                    negotiated_version, cipher_suite)

    except TimeoutError:
        logger.warning("TLS handshake timeout: hostname=%r", target.hostname)
        return TLSResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.TIMEOUT,
                message="TLS handshake timed out.",
            ),
        )
    except ssl.SSLError as exc:
        logger.warning("TLS SSL error: hostname=%r type=%s", target.hostname, type(exc).__name__)
        return TLSResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.TLS_ERROR,
                message="TLS handshake failed.",
            ),
        )
    except ConnectionRefusedError:
        logger.warning("TLS connection refused: hostname=%r ip=%r",
                       target.hostname, target.selected_address)
        return TLSResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.NETWORK_ERROR,
                message="Connection refused.",
            ),
        )
    except OSError as exc:
        logger.warning("TLS OS error: hostname=%r type=%s", target.hostname, type(exc).__name__)
        return TLSResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.NETWORK_ERROR,
                message="Network error during TLS handshake.",
            ),
        )

    # ── Per-version probing ────────────────────────────────────────────────────
    tls_1_0 = _probe_version(target, ssl.TLSVersion.TLSv1, connect_timeout)
    tls_1_1 = _probe_version(target, ssl.TLSVersion.TLSv1_1, connect_timeout)
    tls_1_2 = _probe_version(target, ssl.TLSVersion.TLSv1_2, connect_timeout)
    tls_1_3 = _probe_version(target, ssl.TLSVersion.TLSv1_3, connect_timeout)

    return TLSResult(
        available=True,
        negotiated_version=negotiated_version,
        tls_1_0=tls_1_0,
        tls_1_1=tls_1_1,
        tls_1_2=tls_1_2,
        tls_1_3=tls_1_3,
        cipher_suite=cipher_suite,
    )


def _probe_version(
    target: ValidatedTarget,
    version: ssl.TLSVersion,
    timeout: float,
) -> bool:
    """
    Attempt a TLS handshake forcing a specific TLS version.

    Returns True if the handshake succeeds (server supports it),
    False otherwise. Never raises.
    """
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.minimum_version = version
        ctx.maximum_version = version

        with socket.create_connection(
            (target.selected_address, target.port),
            timeout=timeout,
        ) as raw_sock:
            with ctx.wrap_socket(raw_sock, server_hostname=target.hostname):
                return True

    except (ssl.SSLError, OSError, TimeoutError):
        return False


def _parse_version_str(version_str: str | None) -> TLSVersion:
    """
    Convert ssl.SSLSocket.version() string to TLSVersion enum.

    ssl returns e.g. "TLSv1.2", "TLSv1.3". We normalize to our enum.
    """
    if not version_str:
        return TLSVersion.UNKNOWN
    normalized = version_str.upper().replace("TLSV", "TLS ").replace(".", " ", 1)
    # "TLS 1 2" -> needs another fix
    # ssl returns "TLSv1.2" → "TLS 1 2" is wrong. Let's match directly:
    _map = {
        "TLSV1":   TLSVersion.TLS_1_0,
        "TLSV1.1": TLSVersion.TLS_1_1,
        "TLSV1.2": TLSVersion.TLS_1_2,
        "TLSV1.3": TLSVersion.TLS_1_3,
    }
    upper = version_str.upper().replace(" ", "")
    return _map.get(upper, TLSVersion.UNKNOWN)
