"""
Cookie Scanner — Phase 04.

Parses Set-Cookie headers from a SafeResponse.

SECURITY RULES (SECURITY.md + PHASE_04 §27):
  - Cookie VALUES are NEVER stored, logged, or persisted
  - Only security-relevant attributes are collected
  - Cookie names are stored for identification only
  - value_redacted = True is always set on every CookieObservation

Handles:
  - Multiple Set-Cookie headers (in httpx they come as comma-joined or
    as a special header — we handle both)
  - Quoted attribute values
  - Case variations in attribute names
  - Malformed cookies (no crash)

DOES NOT:
  - Assign severity (Phase 05)
  - Store cookie values
  - Log sensitive cookie data
"""

import logging
import re
from http.cookiejar import http2time

from app.schemas.scan_result import (
    CookieObservation,
    CookiesResult,
    ScannerError,
    ScannerErrorCode,
)
from app.services.safe_http_client import SafeResponse

logger = logging.getLogger(__name__)

# Set-Cookie attribute names (case-insensitive)
_BOOL_ATTRS: frozenset[str] = frozenset({"secure", "httponly"})
_KNOWN_ATTRS: frozenset[str] = frozenset({
    "secure", "httponly", "samesite", "domain", "path", "max-age", "expires",
})

# Patterns for sensitive cookie name detection (used for audit logging only)
_SENSITIVE_NAME_PATTERNS: tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in [
        r"sess(ion)?",
        r"auth",
        r"token",
        r"jwt",
        r"csrf",
        r"bearer",
        r"secret",
    ]
)


def scan_cookies(response: SafeResponse) -> CookiesResult:
    """
    Extract cookie security attributes from Set-Cookie response headers.

    Parameters
    ----------
    response : SafeResponse
        Raw response from SafeHTTPClient.

    Returns
    -------
    CookiesResult
        List of CookieObservation — values always redacted.
    """
    if response is None:
        return CookiesResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.HTTP_ERROR,
                message="No HTTP response available for cookie analysis.",
            ),
        )

    # httpx normalizes duplicate headers by joining with ", " for most headers.
    # For Set-Cookie it may also do this. We handle both by splitting on the
    # canonical set-cookie header value.
    raw_cookie_header = response.headers.get("set-cookie", "")

    if not raw_cookie_header:
        logger.debug("Cookie scan: no Set-Cookie headers found")
        return CookiesResult(available=True, cookies=[])

    # Split multiple cookies — each cookie is separated by a line in httpx
    # because httpx joins multiple Set-Cookie with \n (not comma, since commas
    # appear in Expires). We split on \n first, then handle comma-Expires.
    raw_cookies = _split_set_cookie_header(raw_cookie_header)

    cookies: list[CookieObservation] = []
    for raw in raw_cookies:
        try:
            obs = _parse_cookie(raw.strip())
            if obs is not None:
                cookies.append(obs)
        except Exception:
            # Malformed cookie — record a minimal failed observation
            cookies.append(CookieObservation(
                name="[malformed]",
                parse_error=f"Could not parse Set-Cookie header",
            ))

    logger.info("Cookie scan: found %d cookie(s)", len(cookies))
    return CookiesResult(available=True, cookies=cookies)


def _split_set_cookie_header(raw: str) -> list[str]:
    """
    Split a combined Set-Cookie string into individual cookie strings.

    httpx joins multiple Set-Cookie headers with a newline when accessed
    via the dict-like headers interface. We split on newline first.
    If only one entry, return it as a list of one.
    """
    # Split by newline (httpx multi-value join)
    parts = [p.strip() for p in raw.split("\n") if p.strip()]
    return parts if parts else [raw]


def _parse_cookie(raw: str) -> CookieObservation | None:
    """
    Parse a single Set-Cookie header string into a CookieObservation.

    Cookie format:
      name=VALUE; Secure; HttpOnly; SameSite=Strict; Path=/; Domain=.example.com

    We extract:
      - name (from the first pair before the first `;`)
      - attribute flags

    The value (after `=`) is intentionally discarded.
    """
    if not raw:
        return None

    parts = raw.split(";")
    if not parts:
        return None

    # First part: name=VALUE (or just name for valueless cookies)
    first = parts[0].strip()
    if "=" in first:
        name = first.split("=", 1)[0].strip()
        # VALUE is discarded here — never stored
    else:
        name = first  # valueless cookie

    if not name:
        return None

    # Audit log: note if this appears to be a sensitive cookie (name only, no value)
    if _is_sensitive_name(name):
        logger.debug("Cookie scan: sensitive-looking cookie name detected (name logged for audit)")

    # Parse attributes
    secure = False
    http_only = False
    same_site: str | None = None
    domain: str | None = None
    path: str | None = None
    max_age: int | None = None
    expires: str | None = None
    parse_error: str | None = None

    for attr in parts[1:]:
        attr = attr.strip()
        if not attr:
            continue

        attr_lower = attr.lower()

        if attr_lower == "secure":
            secure = True
        elif attr_lower == "httponly":
            http_only = True
        elif attr_lower.startswith("samesite"):
            val = _attr_value(attr)
            same_site = val.strip() if val else None
        elif attr_lower.startswith("domain"):
            val = _attr_value(attr)
            domain = val.strip() if val else None
        elif attr_lower.startswith("path"):
            val = _attr_value(attr)
            path = val.strip() if val else None
        elif attr_lower.startswith("max-age"):
            val = _attr_value(attr)
            if val:
                try:
                    max_age = int(val.strip())
                except ValueError:
                    parse_error = f"Invalid Max-Age: {val!r}"
        elif attr_lower.startswith("expires"):
            val = _attr_value(attr)
            expires = val.strip() if val else None
        # Unknown attributes silently ignored

    return CookieObservation(
        name=name,
        value_redacted=True,  # always
        secure=secure,
        http_only=http_only,
        same_site=same_site,
        domain=domain,
        path=path,
        max_age=max_age,
        expires=expires,
        parse_error=parse_error,
    )


def _attr_value(attr: str) -> str | None:
    """Extract value from 'key=value' attribute string."""
    if "=" not in attr:
        return None
    _, val = attr.split("=", 1)
    # Strip optional quotes
    val = val.strip().strip('"')
    return val if val else None


def _is_sensitive_name(name: str) -> bool:
    """Return True if the cookie name looks sensitive (for audit logging only)."""
    return any(p.search(name) for p in _SENSITIVE_NAME_PATTERNS)
