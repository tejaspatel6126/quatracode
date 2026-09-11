"""
Header Scanner — Phase 04.

Inspects HTTP security response headers from a SafeResponse.
All header names are treated case-insensitively.

Inspects (per SCANNER_SPECIFICATION.md §16):
  - Strict-Transport-Security (HSTS)
  - Content-Security-Policy (CSP)
  - X-Content-Type-Options
  - X-Frame-Options + CSP frame-ancestors (frame protection)
  - Referrer-Policy
  - Permissions-Policy

DOES NOT:
  - Assign severity
  - Calculate risk
  - Make finding decisions (Phase 05)
"""

import logging
import re

from app.schemas.scan_result import (
    CSPObservation,
    FrameProtectionObservation,
    HSTSObservation,
    HeaderObservation,
    HeadersResult,
    ScannerError,
    ScannerErrorCode,
)
from app.services.safe_http_client import SafeResponse

logger = logging.getLogger(__name__)

# Known valid Referrer-Policy values (spec-defined)
_KNOWN_REFERRER_POLICIES: frozenset[str] = frozenset({
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
    "",  # empty is valid (browser default)
})


def scan_headers(response: SafeResponse) -> HeadersResult:
    """
    Parse all security headers from a SafeResponse.

    Parameters
    ----------
    response : SafeResponse
        Raw response from SafeHTTPClient (headers are pre-lowercased).

    Returns
    -------
    HeadersResult
        Structured raw header observations.
    """
    if response is None:
        return HeadersResult(
            available=False,
            error=ScannerError(
                code=ScannerErrorCode.HTTP_ERROR,
                message="No HTTP response available for header analysis.",
            ),
        )

    headers = response.headers  # already lowercased keys by SafeHTTPClient

    logger.info("Header scan: analyzing %d response headers", len(headers))

    return HeadersResult(
        available=True,
        hsts=_parse_hsts(headers),
        csp=_parse_csp(headers),
        x_content_type_options=_parse_x_content_type_options(headers),
        frame_protection=_parse_frame_protection(headers),
        referrer_policy=_parse_referrer_policy(headers),
        permissions_policy=_parse_permissions_policy(headers),
    )


# ── HSTS parser ────────────────────────────────────────────────────────────────

def _parse_hsts(headers: dict[str, str]) -> HSTSObservation:
    """
    Parse Strict-Transport-Security header.

    Example: max-age=31536000; includeSubDomains; preload
    Malformed values are captured without crashing.
    """
    raw = headers.get("strict-transport-security")
    if raw is None:
        return HSTSObservation(present=False)

    max_age: int | None = None
    include_subdomains = False
    preload = False
    parse_error: str | None = None

    try:
        directives = [d.strip() for d in raw.split(";") if d.strip()]
        for directive in directives:
            lower = directive.lower()
            if lower.startswith("max-age"):
                parts = directive.split("=", 1)
                if len(parts) == 2:
                    try:
                        max_age = int(parts[1].strip())
                    except ValueError:
                        parse_error = f"Invalid max-age value: {parts[1].strip()!r}"
                else:
                    parse_error = "max-age directive missing value"
            elif lower == "includesubdomains":
                include_subdomains = True
            elif lower == "preload":
                preload = True
            # Unknown directives are silently ignored (spec allows extension)
    except Exception as exc:
        parse_error = f"HSTS parse error: {type(exc).__name__}"

    return HSTSObservation(
        present=True,
        raw_value=raw,
        max_age=max_age,
        include_subdomains=include_subdomains,
        preload=preload,
        parse_error=parse_error,
    )


# ── CSP parser ─────────────────────────────────────────────────────────────────

def _parse_csp(headers: dict[str, str]) -> CSPObservation:
    """
    Parse Content-Security-Policy header.

    Handles missing, single, and (in case of dict-based headers) multiple values.
    Extracts directive names only — policy quality is Phase 05.
    """
    raw = headers.get("content-security-policy")
    if raw is None:
        return CSPObservation(present=False)

    directive_names: list[str] = []
    parse_error: str | None = None

    try:
        # Directives are semicolon-separated; each starts with the directive name
        directives = [d.strip() for d in raw.split(";") if d.strip()]
        for directive in directives:
            name = directive.split()[0].lower() if directive.split() else ""
            if name:
                directive_names.append(name)
        directive_names = sorted(set(directive_names))  # deduplicate, sort (deterministic)
    except Exception as exc:
        parse_error = f"CSP parse error: {type(exc).__name__}"

    return CSPObservation(
        present=True,
        raw_value=raw,
        directive_names=directive_names,
        parse_error=parse_error,
    )


# ── X-Content-Type-Options ────────────────────────────────────────────────────

def _parse_x_content_type_options(headers: dict[str, str]) -> HeaderObservation:
    """
    Check X-Content-Type-Options header.
    Expected secure value: 'nosniff'
    """
    raw = headers.get("x-content-type-options")
    present = raw is not None
    normalized = raw.strip().lower() if raw else None
    return HeaderObservation(
        header_name="X-Content-Type-Options",
        present=present,
        raw_value=raw,
        normalized_value=normalized,
    )


# ── Frame protection ──────────────────────────────────────────────────────────

def _parse_frame_protection(headers: dict[str, str]) -> FrameProtectionObservation:
    """
    Inspect X-Frame-Options and CSP frame-ancestors independently.
    Phase 05 will determine which provides stronger protection.
    """
    xfo_raw = headers.get("x-frame-options")
    csp_raw = headers.get("content-security-policy")

    # Extract frame-ancestors from CSP if present
    frame_ancestors_value: str | None = None
    if csp_raw:
        try:
            match = re.search(r'frame-ancestors\s+([^;]+)', csp_raw, re.IGNORECASE)
            if match:
                frame_ancestors_value = match.group(1).strip()
        except Exception:
            pass

    return FrameProtectionObservation(
        x_frame_options_present=xfo_raw is not None,
        x_frame_options_value=xfo_raw,
        csp_frame_ancestors_present=frame_ancestors_value is not None,
        csp_frame_ancestors_value=frame_ancestors_value,
    )


# ── Referrer-Policy ────────────────────────────────────────────────────────────

def _parse_referrer_policy(headers: dict[str, str]) -> HeaderObservation:
    """
    Inspect Referrer-Policy header.
    Unknown values are captured without crashing.
    """
    raw = headers.get("referrer-policy")
    present = raw is not None
    normalized = raw.strip().lower() if raw else None
    parse_error: str | None = None

    if normalized is not None and normalized not in _KNOWN_REFERRER_POLICIES:
        parse_error = f"Unknown Referrer-Policy value: {normalized!r}"

    return HeaderObservation(
        header_name="Referrer-Policy",
        present=present,
        raw_value=raw,
        normalized_value=normalized,
        parse_error=parse_error,
    )


# ── Permissions-Policy ────────────────────────────────────────────────────────

def _parse_permissions_policy(headers: dict[str, str]) -> HeaderObservation:
    """
    Inspect Permissions-Policy header.
    No quality scoring — Phase 05's job.
    """
    raw = headers.get("permissions-policy")
    present = raw is not None
    normalized = raw.strip() if raw else None
    return HeaderObservation(
        header_name="Permissions-Policy",
        present=present,
        raw_value=raw,
        normalized_value=normalized,
    )
