"""
IP address classifier — SSRF/Phase 03.

Uses Python's stdlib ipaddress module exclusively.
NO manual string prefix matching (no ip.startswith("10.") etc.).

Classification categories follow SECURITY.md §9, §10 and PHASE_03 §10-14.

Security invariants guaranteed by this module:
  - Private IPv4 (RFC 1918) is detected.
  - Loopback (127.0.0.0/8, ::1) is detected.
  - Link-local (169.254.0.0/16, fe80::/10) is detected.
  - Cloud metadata (169.254.169.254) is detected.
  - Multicast is detected.
  - Reserved/special-purpose is detected.
  - IPv4-mapped IPv6 (::ffff:x.x.x.x) is unwrapped and the underlying
    IPv4 address is classified — it cannot bypass IPv4 protection.
"""

import ipaddress
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class IPCategory(Enum):
    PUBLIC       = auto()   # Routable public address — safe to scan
    LOOPBACK     = auto()   # 127.0.0.0/8 or ::1
    PRIVATE      = auto()   # RFC 1918 private ranges
    LINK_LOCAL   = auto()   # 169.254.0.0/16 or fe80::/10
    MULTICAST    = auto()   # 224.0.0.0/4 or ff00::/8
    RESERVED     = auto()   # IANA reserved / special-purpose
    UNSPECIFIED  = auto()   # 0.0.0.0 or ::


# ── Cloud metadata addresses (SECURITY.md §10) ────────────────────────────────
# 169.254.169.254 is already link-local but we name it explicitly for auditing.
_METADATA_ADDRESSES: frozenset[ipaddress.IPv4Address] = frozenset({
    ipaddress.IPv4Address("169.254.169.254"),
})


def classify_ip(addr_str: str) -> IPCategory:
    """
    Classify an IP address string into an IPCategory.

    Handles:
      - IPv4
      - IPv6
      - IPv4-mapped IPv6 (::ffff:x.x.x.x) — unwrapped to IPv4 before classification

    Raises ValueError for invalid input (caller handles this).
    """
    try:
        addr = ipaddress.ip_address(addr_str)
    except ValueError:
        raise ValueError(f"Invalid IP address: {addr_str!r}")

    return _classify(addr)


def _classify(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> IPCategory:
    """Internal classification — operates on parsed ipaddress objects."""

    # ── IPv4-mapped IPv6 unwrapping (PHASE_03 §15, SECURITY.md §9) ────────────
    # ::ffff:127.0.0.1 must be treated as 127.0.0.1, not as a public IPv6.
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
        logger.debug("IPv4-mapped IPv6 %s unwrapped to %s", addr, addr.ipv4_mapped)
        return _classify(addr.ipv4_mapped)

    # ── Unspecified (0.0.0.0 / ::) ────────────────────────────────────────────
    if addr.is_unspecified:
        return IPCategory.UNSPECIFIED

    # ── Loopback (127.0.0.0/8, ::1) ───────────────────────────────────────────
    if addr.is_loopback:
        return IPCategory.LOOPBACK

    # ── Link-local (169.254.0.0/16, fe80::/10) ────────────────────────────────
    if addr.is_link_local:
        return IPCategory.LINK_LOCAL

    # ── Private (RFC 1918: 10/8, 172.16/12, 192.168/16; fc00::/7) ─────────────
    if addr.is_private:
        return IPCategory.PRIVATE

    # ── Multicast (224.0.0.0/4, ff00::/8) ────────────────────────────────────
    if addr.is_multicast:
        return IPCategory.MULTICAST

    # ── Reserved / special-purpose ────────────────────────────────────────────
    if addr.is_reserved:
        return IPCategory.RESERVED

    return IPCategory.PUBLIC


def is_safe_for_scanning(addr_str: str) -> bool:
    """
    Return True only if the address is PUBLIC and safe to scan.
    Returns False for ALL other categories including RESERVED.
    """
    try:
        category = classify_ip(addr_str)
        return category == IPCategory.PUBLIC
    except ValueError:
        return False


def is_metadata_address(addr_str: str) -> bool:
    """
    Explicit check for well-known cloud metadata addresses.
    Called in addition to general classification for audit logging clarity.
    """
    try:
        addr = ipaddress.ip_address(addr_str)
        # Unwrap IPv4-mapped IPv6
        if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped is not None:
            addr = addr.ipv4_mapped
        if isinstance(addr, ipaddress.IPv4Address):
            return addr in _METADATA_ADDRESSES
    except ValueError:
        pass
    return False
