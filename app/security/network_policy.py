"""
Network security policy — Phase 03.

Central authority for all outbound connection policy decisions.
Scanners and the Safe HTTP Client consult this module. They do NOT implement
policy independently.

Responsibilities:
  - Scheme allowlist
  - Port allowlist
  - IP category → allow/block decision with specific error code
  - Redirect destination policy
  - Timeout/response-size limits (loaded from settings)

SECURITY RULE: Fail closed — if a decision is ambiguous, block.
"""

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.ip_classifier import IPCategory, classify_ip, is_metadata_address

logger = logging.getLogger(__name__)


# ── Policy constants derived from settings ────────────────────────────────────

def _get_allowed_schemes() -> frozenset[str]:
    settings = get_settings()
    return frozenset(s.strip().lower() for s in settings.ALLOWED_SCHEMES.split(",") if s.strip())


def _get_allowed_ports() -> frozenset[int]:
    settings = get_settings()
    return frozenset(
        int(p.strip()) for p in settings.ALLOWED_PORTS.split(",") if p.strip().isdigit()
    )


# Default ports per scheme (SECURITY.md §14)
_SCHEME_DEFAULT_PORTS: dict[str, int] = {
    "http":  80,
    "https": 443,
}


# ── Scheme policy ─────────────────────────────────────────────────────────────

def assert_scheme_allowed(scheme: str) -> None:
    """
    Raise TargetSecurityError(UNSUPPORTED_SCHEME) if scheme is not allowed.
    Allowed schemes come from settings.ALLOWED_SCHEMES.
    """
    allowed = _get_allowed_schemes()
    if scheme.lower() not in allowed:
        logger.warning("Scheme blocked: %r", scheme)
        raise TargetSecurityError(
            code=SecurityCode.UNSUPPORTED_SCHEME,
            message=f"Scheme '{scheme}' is not supported. Allowed: {sorted(allowed)}.",
        )


# ── Port policy ───────────────────────────────────────────────────────────────

def assert_port_allowed(scheme: str, port: int | None) -> int:
    """
    Validate the port and return the effective port.

    - None → use scheme default.
    - Any port not in the allowlist → INVALID_PORT.

    Returns the effective port number.
    """
    allowed_ports = _get_allowed_ports()
    default_port = _SCHEME_DEFAULT_PORTS.get(scheme.lower())

    effective_port = port if port is not None else default_port

    if effective_port is None:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_PORT,
            message="Cannot determine a valid port for the given scheme.",
        )

    if effective_port not in allowed_ports:
        logger.warning("Port blocked: %d for scheme %r", effective_port, scheme)
        raise TargetSecurityError(
            code=SecurityCode.INVALID_PORT,
            message=(
                f"Port {effective_port} is not permitted. "
                f"Allowed ports: {sorted(allowed_ports)}."
            ),
        )

    return effective_port


# ── IP classification policy ──────────────────────────────────────────────────

def assert_ip_allowed(addr_str: str) -> None:
    """
    Classify an IP address and raise TargetSecurityError if it is not
    safe for outbound scanner requests.

    Handles IPv4, IPv6, and IPv4-mapped IPv6 transparently.

    Security: explicit metadata check is performed first for audit clarity.
    """
    # Cloud metadata — explicit check first (SECURITY.md §10, PHASE_03 §14)
    if is_metadata_address(addr_str):
        logger.warning("Cloud metadata address blocked: %s", addr_str)
        raise TargetSecurityError(
            code=SecurityCode.METADATA_IP_BLOCKED,
            message="Cloud metadata endpoints cannot be scanned.",
        )

    try:
        category = classify_ip(addr_str)
    except ValueError:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_HOSTNAME,
            message="Could not classify the resolved IP address.",
        )

    _CATEGORY_ERROR: dict[IPCategory, tuple[str, str]] = {
        IPCategory.LOOPBACK:    (SecurityCode.LOOPBACK_BLOCKED,   "Loopback addresses cannot be scanned."),
        IPCategory.PRIVATE:     (SecurityCode.PRIVATE_IP_BLOCKED,  "Private/internal addresses cannot be scanned."),
        IPCategory.LINK_LOCAL:  (SecurityCode.LINK_LOCAL_BLOCKED,  "Link-local addresses cannot be scanned."),
        IPCategory.MULTICAST:   (SecurityCode.MULTICAST_IP_BLOCKED,"Multicast addresses cannot be scanned."),
        IPCategory.RESERVED:    (SecurityCode.RESERVED_IP_BLOCKED, "Reserved/special-purpose addresses cannot be scanned."),
        IPCategory.UNSPECIFIED: (SecurityCode.RESERVED_IP_BLOCKED, "Unspecified addresses cannot be scanned."),
    }

    if category in _CATEGORY_ERROR:
        code, message = _CATEGORY_ERROR[category]
        logger.warning("IP blocked: %s (category=%s)", addr_str, category.name)
        raise TargetSecurityError(code=code, message=message)

    # IPCategory.PUBLIC — allowed
    logger.debug("IP allowed: %s (category=%s)", addr_str, category.name)


# ── All-addresses policy (multiple DNS records) ───────────────────────────────

def assert_all_addresses_allowed(addresses: tuple[str, ...]) -> None:
    """
    Verify that EVERY resolved address is safe.

    Per PHASE_03 §16: if ANY address in the result set is unsafe, the target
    is rejected. We do not silently discard unsafe addresses and connect to
    a remaining public one — that would be undefined behavior.

    Raises TargetSecurityError on the first blocked address.
    """
    for addr in addresses:
        assert_ip_allowed(addr)
