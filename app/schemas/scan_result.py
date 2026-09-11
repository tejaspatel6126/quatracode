"""
app/schemas/scan_result.py  — Phase 04 raw observation model.

Defines the data structures that the scanner produces.
These are RAW OBSERVATIONS — no severity, no risk score, no AI.

Severity and findings live in Phase 05.

Design rules:
  - Pydantic models only (consistent with the existing schema layer)
  - All fields type-annotated
  - Stable field names (check_ids must not be renamed after they ship)
  - No sensitive data (no private keys, no cookie values, no passwords)
  - Serializable to JSON
  - Deterministic field ordering
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Check IDs (SCANNER_SPECIFICATION.md §45) ────────────────────────────────────
# Stable identifiers — do NOT rename after they ship.

class CheckId:
    # TLS
    TLS_PROTOCOL            = "TLS_PROTOCOL"
    TLS_CERTIFICATE         = "TLS_CERTIFICATE"
    TLS_CERT_EXPIRY         = "TLS_CERT_EXPIRY"
    TLS_CERT_HOSTNAME       = "TLS_CERT_HOSTNAME"
    TLS_CERT_SELF_SIGNED    = "TLS_CERT_SELF_SIGNED"
    TLS_CERT_CHAIN          = "TLS_CERT_CHAIN"

    # HTTP headers
    HTTP_HSTS               = "HTTP_HSTS"
    HTTP_CSP                = "HTTP_CSP"
    HTTP_X_CONTENT_TYPE_OPTIONS = "HTTP_X_CONTENT_TYPE_OPTIONS"
    HTTP_FRAME_PROTECTION   = "HTTP_FRAME_PROTECTION"
    HTTP_REFERRER_POLICY    = "HTTP_REFERRER_POLICY"
    HTTP_PERMISSIONS_POLICY = "HTTP_PERMISSIONS_POLICY"

    # Cookies
    HTTP_COOKIE_SECURITY    = "HTTP_COOKIE_SECURITY"

    # Redirect / enforcement
    HTTP_HTTPS_REDIRECT     = "HTTP_HTTPS_REDIRECT"


# ── Scanner module names ────────────────────────────────────────────────────────

class ScannerModule(str, Enum):
    TLS         = "tls"
    CERTIFICATE = "certificate"
    HTTP        = "http"
    HEADERS     = "headers"
    COOKIES     = "cookies"
    REDIRECTS   = "redirects"
    NETWORK     = "network"  # Phase 04 Nmap network discovery


# ── Module / scan status ───────────────────────────────────────────────────────

class ModuleStatus(str, Enum):
    COMPLETED   = "completed"
    FAILED      = "failed"
    SKIPPED     = "skipped"


class ScanStatus(str, Enum):
    COMPLETED   = "completed"
    PARTIAL     = "partial"    # some modules failed, others succeeded
    FAILED      = "failed"


# ── Scanner error codes (PHASE_04 §40) ─────────────────────────────────────────

class ScannerErrorCode(str, Enum):
    NETWORK_ERROR       = "NETWORK_ERROR"
    TLS_ERROR           = "TLS_ERROR"
    CERTIFICATE_ERROR   = "CERTIFICATE_ERROR"
    HTTP_ERROR          = "HTTP_ERROR"
    TIMEOUT             = "TIMEOUT"
    PARSER_ERROR        = "PARSER_ERROR"
    UNSUPPORTED_TARGET  = "UNSUPPORTED_TARGET"
    SCAN_MODULE_ERROR   = "SCAN_MODULE_ERROR"
    RESPONSE_TOO_LARGE  = "RESPONSE_TOO_LARGE"
    REDIRECT_ERROR      = "REDIRECT_ERROR"


# ── Structured scanner error ───────────────────────────────────────────────────

class ScannerError(BaseModel):
    """Structured scanner error — no stack traces in API output."""
    code: ScannerErrorCode
    message: str
    module: ScannerModule | None = None


# ── TLS protocol versions ─────────────────────────────────────────────────────

class TLSVersion(str, Enum):
    TLS_1_0     = "TLS 1.0"
    TLS_1_1     = "TLS 1.1"
    TLS_1_2     = "TLS 1.2"
    TLS_1_3     = "TLS 1.3"
    UNKNOWN     = "UNKNOWN"


# ── Certificate validity states ───────────────────────────────────────────────

class CertValidityState(str, Enum):
    NOT_YET_VALID   = "NOT_YET_VALID"
    VALID           = "VALID"
    EXPIRED         = "EXPIRED"
    UNKNOWN         = "UNKNOWN"


class CertHostnameState(str, Enum):
    MATCH                   = "MATCH"
    MISMATCH                = "MISMATCH"
    VALIDATION_UNAVAILABLE  = "VALIDATION_UNAVAILABLE"


# ── HSTS observation ──────────────────────────────────────────────────────────

class HSTSObservation(BaseModel):
    present: bool
    raw_value: str | None = None
    max_age: int | None = None                  # seconds
    include_subdomains: bool = False
    preload: bool = False
    parse_error: str | None = None              # non-None if malformed


# ── CSP observation ───────────────────────────────────────────────────────────

class CSPObservation(BaseModel):
    present: bool
    raw_value: str | None = None                # joined if duplicate headers
    directive_names: list[str] = Field(default_factory=list)
    parse_error: str | None = None


# ── Generic header presence model ────────────────────────────────────────────

class HeaderObservation(BaseModel):
    """Minimal presence + raw value for a single security header."""
    header_name: str
    present: bool
    raw_value: str | None = None
    normalized_value: str | None = None         # lowercased, stripped
    parse_error: str | None = None


# ── Frame protection (covers both X-Frame-Options and CSP frame-ancestors) ────

class FrameProtectionObservation(BaseModel):
    x_frame_options_present: bool = False
    x_frame_options_value: str | None = None
    csp_frame_ancestors_present: bool = False
    csp_frame_ancestors_value: str | None = None


# ── Cookie observation ────────────────────────────────────────────────────────

class CookieObservation(BaseModel):
    """
    Attributes of a single Set-Cookie header.
    Cookie values are REDACTED — only metadata is stored.
    """
    name: str                               # cookie name (may be redacted for sensitive names)
    value_redacted: bool = True             # always True — we never store cookie values
    secure: bool = False
    http_only: bool = False
    same_site: str | None = None            # "Strict" | "Lax" | "None" | None (missing)
    domain: str | None = None
    path: str | None = None
    max_age: int | None = None
    expires: str | None = None              # raw Expires string, not parsed to datetime
    parse_error: str | None = None


# ── Redirect step ─────────────────────────────────────────────────────────────

class RedirectStep(BaseModel):
    step: int
    from_url: str
    status_code: int
    location: str | None = None


# ── TLS module result ─────────────────────────────────────────────────────────

class TLSResult(BaseModel):
    """Raw TLS handshake observations."""
    available: bool                         # TLS successfully negotiated
    negotiated_version: TLSVersion | None = None
    # Per-version negotiation support (attempt to negotiate each)
    tls_1_0: bool | None = None
    tls_1_1: bool | None = None
    tls_1_2: bool | None = None
    tls_1_3: bool | None = None
    cipher_suite: str | None = None
    error: ScannerError | None = None


# ── Certificate module result ─────────────────────────────────────────────────

class CertificateResult(BaseModel):
    """Raw certificate metadata observations. No private material ever stored."""
    available: bool
    subject: dict[str, str] | None = None
    issuer: dict[str, str] | None = None
    serial_number: str | None = None
    valid_from: datetime.datetime | None = None
    valid_until: datetime.datetime | None = None
    san_entries: list[str] = Field(default_factory=list)
    signature_algorithm: str | None = None
    public_key_algorithm: str | None = None
    public_key_size: int | None = None
    # Validity analysis
    validity_state: CertValidityState = CertValidityState.UNKNOWN
    is_expired: bool | None = None
    days_until_expiry: int | None = None
    hostname_validation: CertHostnameState = CertHostnameState.VALIDATION_UNAVAILABLE
    is_self_signed: bool | None = None
    # Chain info
    chain_length: int | None = None
    chain_trusted: bool | None = None
    chain_error: str | None = None
    error: ScannerError | None = None


# ── HTTP module result ────────────────────────────────────────────────────────

class HTTPResult(BaseModel):
    """Raw HTTP response observations (headers, status, redirects)."""
    available: bool
    status_code: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    server: str | None = None              # Server header (informational only)
    redirect_count: int = 0
    error: ScannerError | None = None


# ── Headers module result ─────────────────────────────────────────────────────

class HeadersResult(BaseModel):
    """Raw security header observations."""
    available: bool = True
    hsts: HSTSObservation | None = None
    csp: CSPObservation | None = None
    x_content_type_options: HeaderObservation | None = None
    frame_protection: FrameProtectionObservation | None = None
    referrer_policy: HeaderObservation | None = None
    permissions_policy: HeaderObservation | None = None
    error: ScannerError | None = None


# ── Cookies module result ─────────────────────────────────────────────────────

class CookiesResult(BaseModel):
    """Raw cookie attribute observations."""
    available: bool = True
    cookies: list[CookieObservation] = Field(default_factory=list)
    error: ScannerError | None = None


# ── Redirects module result ───────────────────────────────────────────────────

class RedirectsResult(BaseModel):
    """Raw redirect-chain observations."""
    available: bool = True
    initial_url: str | None = None
    final_url: str | None = None
    final_scheme: str | None = None
    redirect_count: int = 0
    redirect_chain: list[RedirectStep] = Field(default_factory=list)
    https_redirect_observed: bool = False
    error: ScannerError | None = None


# ── Per-module wrapper ────────────────────────────────────────────────────────

class ModuleResult(BaseModel):
    """Wraps a scanner module result with execution status."""
    module: ScannerModule
    status: ModuleStatus
    error: ScannerError | None = None


# ── Top-level scan result ──────────────────────────────────────────────────────

class ScanResult(BaseModel):
    """
    Complete Phase 04 raw scan output.

    No severity. No risk. No AI. Just facts.
    Phase 05 will interpret these observations.
    """
    # Scan metadata
    target_url: str
    target_hostname: str
    target_scheme: str
    scanner_version: str = "0.4.0"
    started_at: datetime.datetime
    completed_at: datetime.datetime | None = None
    status: ScanStatus = ScanStatus.COMPLETED

    # Module results (None = not attempted)
    tls: TLSResult | None = None
    certificate: CertificateResult | None = None
    http: HTTPResult | None = None
    headers: HeadersResult | None = None
    cookies: CookiesResult | None = None
    redirects: RedirectsResult | None = None
    network: Any | None = None  # NmapResult — Any avoids circular import

    # Module execution status (always populated)
    module_statuses: list[ModuleResult] = Field(default_factory=list)

    # Scan-level error (only set if overall scan could not start)
    scan_error: ScannerError | None = None
