"""
Target URL validator — Phase 03 core security boundary.

MANDATORY INVARIANT: A raw user-controlled URL must NEVER be passed directly
to any network client. Every outbound connection must go through:

    validate_target(user_url)  ->  ValidatedTarget
    safe_request(validated_target)

Validation pipeline (SECURITY.md §6, PHASE_03 §5):
    1. Parse — standard library urllib.parse
    2. Normalize — scheme/hostname casing, strip whitespace
    3. Structural validation — scheme, credentials, hostname, port
    4. DNS resolution — resolve ALL addresses
    5. IP classification — check EVERY resolved address
    6. Network policy — block unsafe destinations
    7. Return ValidatedTarget — immutable structured result

Security decisions:
  - Credentials in URL are rejected before any DNS lookup.
  - If ANY resolved address is unsafe, the target is blocked.
  - DNS is always performed before connection (no hostname-trust).
  - The validated result stores all resolved addresses for DNS-rebinding
    protection: the Safe HTTP Client pins the connection to selected_address
    rather than re-resolving.

Logging:
  - Only hostname is logged, NEVER full URL (could contain credentials).
  - Error messages are safe for API responses.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from app.core.config import get_settings
from app.security.dns_resolver import DNSResult, resolve_hostname
from app.security.errors import SecurityCode, TargetSecurityError
from app.security.network_policy import (
    assert_all_addresses_allowed,
    assert_port_allowed,
    assert_scheme_allowed,
)

logger = logging.getLogger(__name__)

# Maximum URL length to accept (prevents memory/parsing DOS)
_MAX_URL_LENGTH = 2048
# Maximum hostname length (RFC 1034)
_MAX_HOSTNAME_LENGTH = 253
# Valid hostname label characters
_HOSTNAME_LABEL_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$')


@dataclass(frozen=True)
class ValidatedTarget:
    """
    Immutable result of a successful target validation.

    SECURITY: Only pass this object to the Safe HTTP Client.
    Do NOT reconstruct raw URLs from its fields and pass them to other clients.

    The selected_address is the IP address that MUST be used for the connection
    (DNS-rebinding protection — prevents a fresh DNS lookup after validation).
    """
    normalized_url: str       # Safe URL for display (credentials stripped)
    scheme: str               # "http" or "https"
    hostname: str             # Normalized hostname
    port: int                 # Effective port (80 or 443)
    path: str                 # URL path component
    query: str                # URL query component
    dns_result: DNSResult     # All resolved addresses
    selected_address: str     # The specific IP chosen for connection


# ── Step 1: Input sanitization ────────────────────────────────────────────────

def _sanitize_raw_input(raw_url: str) -> str:
    """
    Reject obviously malformed input and return a cleaned string.

    Rejects:
      - Non-string input
      - Excessive length (>2048 chars)
      - Control characters (including null bytes, CRLF)
    """
    if not isinstance(raw_url, str):
        raise TargetSecurityError(
            code=SecurityCode.INVALID_URL,
            message="URL must be a string.",
        )

    # Strip leading/trailing whitespace (common user mistake)
    url = raw_url.strip()

    if not url:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_URL,
            message="URL must not be empty.",
        )

    if len(url) > _MAX_URL_LENGTH:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_URL,
            message=f"URL exceeds maximum length of {_MAX_URL_LENGTH} characters.",
        )

    # Reject control characters (CRLF injection, null bytes, etc.)
    for char in url:
        cat = unicodedata.category(char)
        if cat.startswith("C"):  # Control, Format, Surrogate, Private-use, Unassigned
            raise TargetSecurityError(
                code=SecurityCode.INVALID_URL,
                message="URL contains invalid control characters.",
            )

    return url


# ── Step 2: Parse ──────────────────────────────────────────────────────────────

def _parse_url(url: str):
    """
    Parse the URL using stdlib urlparse.
    Returns ParseResult. Raises TargetSecurityError for structural problems.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_URL,
            message="URL could not be parsed.",
        )

    if not parsed.scheme:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_URL,
            message="URL is missing a scheme (e.g. https://).",
        )

    return parsed


# ── Step 3: Normalize ─────────────────────────────────────────────────────────

def _normalize(parsed) -> tuple:
    """
    Return (scheme, hostname, port, path, query).

    Normalization:
      - Scheme lowercased.
      - Hostname lowercased.
      - Port: None if it equals the scheme default.
    """
    scheme   = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower().strip()
    port     = parsed.port      # None if not explicit in URL
    path     = parsed.path or "/"
    query    = parsed.query or ""
    return scheme, hostname, port, path, query


# ── Step 4: Structural validation ─────────────────────────────────────────────

def _validate_no_credentials(parsed) -> None:
    """
    Reject URLs containing a username or password.
    SECURITY.md §6, PHASE_03 §6.

    SECURITY: Never log the actual username/password.
    """
    if parsed.username is not None or parsed.password is not None:
        raise TargetSecurityError(
            code=SecurityCode.URL_CREDENTIALS_NOT_ALLOWED,
            message="URLs containing embedded credentials are not permitted.",
        )


def _validate_hostname(hostname: str) -> None:
    """
    Validate the normalized hostname.

    Rejects:
      - Empty hostname
      - Hostname exceeding RFC limit
      - Labels with invalid characters
      - Hostnames ending with a dot (technically valid but unusual — reject to reduce attack surface)
      - Numeric-only labels that don't form a valid IP (handled later by DNS)
    """
    if not hostname:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_HOSTNAME,
            message="URL must contain a hostname.",
        )

    if len(hostname) > _MAX_HOSTNAME_LENGTH:
        raise TargetSecurityError(
            code=SecurityCode.INVALID_HOSTNAME,
            message=f"Hostname exceeds maximum length of {_MAX_HOSTNAME_LENGTH} characters.",
        )

    # Strip trailing dot (FQDN) for label validation
    check_hostname = hostname.rstrip(".")

    # IPv6 literal — urlparse gives us the address without brackets
    if ":" in hostname:
        # Will be validated by ipaddress during DNS/IP classification
        return

    # Validate each label
    labels = check_hostname.split(".")
    for label in labels:
        if not label:
            raise TargetSecurityError(
                code=SecurityCode.INVALID_HOSTNAME,
                message="Hostname contains an empty label.",
            )
        if not _HOSTNAME_LABEL_RE.match(label):
            # Allow single-character labels (e.g. "a") and numeric labels for IPs
            if not re.match(r'^[a-zA-Z0-9]$', label):
                raise TargetSecurityError(
                    code=SecurityCode.INVALID_HOSTNAME,
                    message="Hostname contains invalid characters.",
                )


# ── Step 5+6: DNS + IP policy ─────────────────────────────────────────────────

def _resolve_and_classify(
    hostname: str,
    dns_timeout: float,
    resolver,
) -> DNSResult:
    """
    Resolve the hostname and verify all resulting addresses pass security policy.

    resolver: callable with signature (hostname, timeout) -> DNSResult
    Raises TargetSecurityError on DNS failure, empty result, or any unsafe address.
    """
    dns_result = resolver(hostname, timeout=dns_timeout)

    if not dns_result.success:
        error_text = dns_result.error or "DNS resolution failed"
        if "timeout" in error_text.lower():
            raise TargetSecurityError(
                code=SecurityCode.DNS_TIMEOUT,
                message="DNS resolution timed out.",
            )
        raise TargetSecurityError(
            code=SecurityCode.DNS_RESOLUTION_FAILED,
            message="Could not resolve the hostname.",
        )

    if dns_result.is_empty:
        raise TargetSecurityError(
            code=SecurityCode.DNS_EMPTY_RESULT,
            message="The hostname resolved to no addresses.",
        )

    # PHASE_03 §16: If ANY resolved address is unsafe, reject the target.
    # We do NOT silently skip unsafe addresses.
    assert_all_addresses_allowed(dns_result.addresses)

    return dns_result


# ── Public API ────────────────────────────────────────────────────────────────

def validate_target(
    raw_url: str,
    *,
    resolver=None,
) -> ValidatedTarget:
    """
    Validate a user-supplied target URL through the full security pipeline.

    Parameters
    ----------
    raw_url : str
        The untrusted URL supplied by the user.
    resolver : callable, optional
        Inject a custom DNS resolver function for testing.
        Signature: resolver(hostname, timeout) -> DNSResult
        If None, the production resolve_hostname() is used.

    Returns
    -------
    ValidatedTarget
        An immutable validated target safe for passing to the Safe HTTP Client.

    Raises
    ------
    TargetSecurityError
        On any validation failure. Always has a machine-readable code.

    SECURITY RULE: The caller MUST NOT pass raw_url to any network client.
    Only the returned ValidatedTarget should be used for connections.
    """
    settings = get_settings()
    _resolver = resolver or resolve_hostname

    # 1. Sanitize raw input
    url = _sanitize_raw_input(raw_url)

    # 2. Parse
    parsed = _parse_url(url)

    # 3. Normalize
    scheme, hostname, port, path, query = _normalize(parsed)

    # 4a. Credentials check (before logging anything)
    _validate_no_credentials(parsed)

    # 4b. Scheme
    assert_scheme_allowed(scheme)

    # 4c. Hostname
    _validate_hostname(hostname)

    # 4d. Port
    effective_port = assert_port_allowed(scheme, port)

    # Log only hostname — never the full raw_url (could contain credentials)
    logger.info("Validating target: hostname=%r scheme=%r port=%d", hostname, scheme, effective_port)

    # 5+6. DNS resolution + IP classification
    # Use injected resolver if provided (allows mocking in tests)
    dns_result = _resolve_and_classify(
        hostname,
        dns_timeout=settings.DNS_TIMEOUT,
        resolver=_resolver,
    )

    # DNS rebinding protection: select the first validated address.
    # The Safe HTTP Client MUST connect to this specific address rather than
    # performing a new DNS lookup. This eliminates the TOCTOU window.
    selected_address = dns_result.addresses[0]

    # Build a normalized URL (without credentials, with lowercase scheme/host)
    # This is safe to log and return in API responses.
    normalized_url = urlunparse((
        scheme,
        f"{hostname}:{effective_port}" if effective_port not in (80, 443) else hostname,
        path,
        "",     # params — not used
        query,
        "",     # fragment — stripped for security
    ))

    logger.info(
        "Target validated: hostname=%r selected_ip=%r addresses=%s",
        hostname, selected_address, dns_result.addresses,
    )

    return ValidatedTarget(
        normalized_url=normalized_url,
        scheme=scheme,
        hostname=hostname,
        port=effective_port,
        path=path,
        query=query,
        dns_result=dns_result,
        selected_address=selected_address,
    )
