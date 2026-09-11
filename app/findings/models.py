"""
Phase 05 — Finding & Risk Engine domain models.

DESIGN RULES:
  - Severity is assigned by the Finding Engine from documented rules only.
  - No user-controlled severity input accepted.
  - No AI, no probabilistic classification.
  - Every Finding has a stable finding_id that must not be renamed.
  - Evidence must not contain passwords, private keys, session tokens.
  - RiskResult is the authoritative Phase 05 output consumed by Phase 06+.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Severity ──────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    """
    Severity levels — defined by SCANNER_SPECIFICATION.md.
    Ordered lowest → highest for comparison operations.
    """
    INFO     = "INFO"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

    def __lt__(self, other: "Severity") -> bool:
        return _SEVERITY_ORDER[self] < _SEVERITY_ORDER[other]

    def __le__(self, other: "Severity") -> bool:
        return _SEVERITY_ORDER[self] <= _SEVERITY_ORDER[other]

    def __gt__(self, other: "Severity") -> bool:
        return _SEVERITY_ORDER[self] > _SEVERITY_ORDER[other]

    def __ge__(self, other: "Severity") -> bool:
        return _SEVERITY_ORDER[self] >= _SEVERITY_ORDER[other]


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.INFO:     0,
    Severity.LOW:      1,
    Severity.MEDIUM:   2,
    Severity.HIGH:     3,
    Severity.CRITICAL: 4,
}


# ── Finding category ──────────────────────────────────────────────────────────

class FindingCategory(str, Enum):
    TLS          = "TLS"
    CERTIFICATE  = "CERTIFICATE"
    HTTP_HEADERS = "HTTP_HEADERS"
    COOKIES      = "COOKIES"
    REDIRECTS    = "REDIRECTS"
    HTTPS        = "HTTPS"
    CONFIGURATION = "CONFIGURATION"


# ── Stable Finding IDs ────────────────────────────────────────────────────────
# From SCANNER_SPECIFICATION.md — must not be renamed after shipping.

class FindingId:
    # TLS Protocol (§14)
    TLS_1_0_ENABLED              = "TLS_1_0_ENABLED"
    TLS_1_1_ENABLED              = "TLS_1_1_ENABLED"

    # Certificate (§8, §10, §11)
    TLS_CERT_EXPIRED             = "TLS_CERT_EXPIRED"
    TLS_CERT_EXPIRY_SOON_HIGH    = "TLS_CERT_EXPIRY_SOON_HIGH"
    TLS_CERT_EXPIRY_SOON_MEDIUM  = "TLS_CERT_EXPIRY_SOON_MEDIUM"
    TLS_CERT_EXPIRY_SOON_LOW     = "TLS_CERT_EXPIRY_SOON_LOW"
    TLS_CERT_HOSTNAME_MISMATCH   = "TLS_CERT_HOSTNAME_MISMATCH"
    TLS_CERT_SELF_SIGNED         = "TLS_CERT_SELF_SIGNED"

    # HTTP Headers (§17–23)
    HTTP_HSTS_MISSING            = "HTTP_HSTS_MISSING"
    HTTP_HSTS_SHORT_MAX_AGE      = "HTTP_HSTS_SHORT_MAX_AGE"
    HTTP_CSP_MISSING             = "HTTP_CSP_MISSING"
    HTTP_CSP_UNSAFE_INLINE       = "HTTP_CSP_UNSAFE_INLINE"
    HTTP_CSP_UNSAFE_EVAL         = "HTTP_CSP_UNSAFE_EVAL"
    HTTP_X_CONTENT_TYPE_MISSING  = "HTTP_X_CONTENT_TYPE_MISSING"
    HTTP_FRAME_PROTECTION_MISSING = "HTTP_FRAME_PROTECTION_MISSING"
    HTTP_REFERRER_POLICY_MISSING = "HTTP_REFERRER_POLICY_MISSING"
    HTTP_REFERRER_POLICY_WEAK    = "HTTP_REFERRER_POLICY_WEAK"
    HTTP_PERMISSIONS_POLICY_MISSING = "HTTP_PERMISSIONS_POLICY_MISSING"

    # Cookies (§26–28)
    HTTP_COOKIE_SECURE_MISSING   = "HTTP_COOKIE_SECURE_MISSING"
    HTTP_COOKIE_HTTPONLY_MISSING  = "HTTP_COOKIE_HTTPONLY_MISSING"
    HTTP_COOKIE_SAMESITE_NONE_INSECURE = "HTTP_COOKIE_SAMESITE_NONE_INSECURE"

    # Redirects (§31–35)
    HTTP_HTTPS_REDIRECT_MISSING  = "HTTP_HTTPS_REDIRECT_MISSING"


# ── Evidence model ────────────────────────────────────────────────────────────

class Evidence(BaseModel):
    """
    Safe, concise evidence for a security finding.

    SECURITY: Must never contain passwords, private keys, session tokens,
    authorization headers, or cookie values.
    """
    observed: str              # What was observed (e.g. "TLS 1.0 is supported")
    detail: str | None = None  # Optional supporting detail (safe text only)

    @field_validator("observed", "detail", mode="before")
    @classmethod
    def _no_empty(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            return None
        return v


# ── Security Finding ──────────────────────────────────────────────────────────

class SecurityFinding(BaseModel):
    """
    Authoritative security finding produced by the Finding Engine.

    finding_id — stable; never rename after shipping
    check_id   — from Phase 04 CheckId constants
    severity   — from documented rules only (never from user input)
    evidence   — safe, concise, no credentials
    remediation — predefined, not AI-generated
    """
    finding_id:   str
    check_id:     str
    category:     FindingCategory
    title:        str
    description:  str
    severity:     Severity
    confidence:   float = Field(default=1.0, ge=0.0, le=1.0)
    evidence:     list[Evidence] = Field(default_factory=list)
    remediation:  str
    references:   list[str] = Field(default_factory=list)
    rule_version: str = "1.0"

    def is_higher_than(self, other: "SecurityFinding") -> bool:
        return self.severity > other.severity


# ── Risk Level ────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    """
    Risk levels derived from score.
    Thresholds from PHASE_05_FINDING_RISK.md §30.
    """
    VERY_LOW = "VERY_LOW"  # 0–19
    LOW      = "LOW"        # 20–39
    MEDIUM   = "MEDIUM"     # 40–59
    HIGH     = "HIGH"       # 60–79
    CRITICAL = "CRITICAL"   # 80–100


# ── Score Contribution ────────────────────────────────────────────────────────

class ScoreContribution(BaseModel):
    finding_id: str
    severity:   Severity
    weight:     float
    contribution: float  # 0-100 normalized contribution to final score


# ── Risk Result ───────────────────────────────────────────────────────────────

class RiskResult(BaseModel):
    """
    Authoritative risk result produced by the Risk Engine.

    This is the Phase 05 output consumed by Phase 06 (persistence) and
    Phase 07+ (API/reports).

    scoring_version — records which calculation formula was used.
    Same findings + same version = same score (deterministic guarantee).
    """
    score:           float = Field(ge=0.0, le=100.0)
    risk_level:      RiskLevel
    finding_count:   int
    severity_counts: dict[str, int]  # {"CRITICAL": 1, "HIGH": 2, ...}
    contributions:   list[ScoreContribution] = Field(default_factory=list)
    scoring_version: str = "1.0"
    findings:        list[SecurityFinding] = Field(default_factory=list)
    computed_at:     datetime.datetime | None = None

    @property
    def has_critical(self) -> bool:
        return self.severity_counts.get("CRITICAL", 0) > 0

    @property
    def has_high(self) -> bool:
        return self.severity_counts.get("HIGH", 0) > 0
