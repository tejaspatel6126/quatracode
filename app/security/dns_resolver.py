"""
DNS resolver abstraction — Phase 03.

Responsibilities:
  - Resolve hostname to IPv4/IPv6 addresses.
  - Enforce DNS timeout.
  - Handle DNS failures safely.
  - Return structured results.
  - Allow mocking in tests (via injectable resolver callable).

SECURITY RULE: DNS is performed BEFORE any network connection.
The resolved addresses are classified by ip_classifier before use.
This module does NOT make policy decisions — it only resolves.
"""

import logging
import socket
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DNSResult:
    """Structured DNS resolution result."""
    hostname: str
    addresses: tuple[str, ...]  # all resolved addresses (IPv4 and IPv6)
    success: bool
    error: str | None = None

    @property
    def is_empty(self) -> bool:
        return self.success and len(self.addresses) == 0


def resolve_hostname(
    hostname: str,
    timeout: float = 5.0,
) -> DNSResult:
    """
    Resolve a hostname to all its IPv4 and IPv6 addresses.

    Uses socket.getaddrinfo which respects /etc/hosts, system DNS, and
    supports both IPv4 and IPv6.

    The timeout is enforced via socket.setdefaulttimeout() scoped to this
    call only — restored afterwards.

    Returns a DNSResult. Never raises; errors are captured in the result.

    SECURITY NOTE: The caller (target_validator) is responsible for classifying
    every address in result.addresses before allowing a connection.
    """
    if not hostname:
        return DNSResult(
            hostname=hostname,
            addresses=(),
            success=False,
            error="Empty hostname",
        )

    # Preserve existing default timeout and restore it after resolution
    original_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        raw = socket.getaddrinfo(
            hostname,
            None,              # port — not needed for address resolution
            socket.AF_UNSPEC,  # IPv4 + IPv6
            socket.SOCK_STREAM,
        )
        # getaddrinfo returns (family, type, proto, canonname, sockaddr)
        # sockaddr is (address, port) for IPv4, (address, port, flow, scope) for IPv6
        addresses = tuple({entry[4][0] for entry in raw})  # deduplicate

        if not addresses:
            return DNSResult(
                hostname=hostname,
                addresses=(),
                success=True,  # resolved but empty
            )

        logger.debug("DNS resolved %r -> %s", hostname, addresses)
        return DNSResult(hostname=hostname, addresses=addresses, success=True)

    except TimeoutError:
        logger.warning("DNS timeout resolving %r", hostname)
        return DNSResult(
            hostname=hostname,
            addresses=(),
            success=False,
            error="DNS timeout",
        )
    except socket.gaierror as exc:
        # Log type only — hostname may be attacker-controlled, but is not a secret
        logger.warning("DNS resolution failed for %r: %s", hostname, type(exc).__name__)
        return DNSResult(
            hostname=hostname,
            addresses=(),
            success=False,
            error=f"DNS resolution failed: {type(exc).__name__}",
        )
    except OSError as exc:
        logger.warning("DNS OS error for %r: %s", hostname, type(exc).__name__)
        return DNSResult(
            hostname=hostname,
            addresses=(),
            success=False,
            error=f"DNS error: {type(exc).__name__}",
        )
    finally:
        socket.setdefaulttimeout(original_timeout)
