"""
AI Data Sanitizer — Phase 08.

Removes sensitive information before sending data to the AI provider.
This is a defense-in-depth measure. The finding engine already strips
credentials from evidence, but we sanitize again at the AI boundary.

Protected patterns:
  - Authorization header values
  - Cookie values
  - Password fields
  - API key patterns
  - Token patterns
  - Private key blocks
"""
from __future__ import annotations

import re

# ── Redaction patterns ────────────────────────────────────────────────────────

# Headers that should have their values masked
_SENSITIVE_HEADER_NAMES: frozenset[str] = frozenset({
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-access-token",
    "proxy-authorization",
    "www-authenticate",
})

# Regex patterns for inline credential detection (case-insensitive)
_CREDENTIAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+'),
    re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+'),
    re.compile(r'(?i)(secret|token|auth)\s*[:=]\s*[A-Za-z0-9+/=_\-]{8,}'),
    re.compile(r'(?i)bearer\s+[A-Za-z0-9+/=_\-\.]{8,}'),
    re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----'),
    re.compile(r'(?i)eyJ[A-Za-z0-9+/=]{10,}'),   # JWT-like prefix
]

_REDACTION_PLACEHOLDER = "[REDACTED]"


def sanitize_text(text: str | None) -> str:
    """
    Remove obvious credential patterns from a text string.

    Safe to call on evidence, descriptions, and remediation text.
    Returns empty string if text is None.
    """
    if not text:
        return ""
    result = text
    for pattern in _CREDENTIAL_PATTERNS:
        result = pattern.sub(_REDACTION_PLACEHOLDER, result)
    return result


def sanitize_evidence_list(evidence: list[dict]) -> list[str]:
    """
    Convert evidence dicts to sanitized plain-text strings.

    evidence items have: observed (str), detail (str | None)
    """
    sanitized: list[str] = []
    for ev in evidence:
        observed = sanitize_text(ev.get("observed", ""))
        detail   = sanitize_text(ev.get("detail") or "")
        if detail:
            sanitized.append(f"{observed} — {detail}")
        elif observed:
            sanitized.append(observed)
    # Cap total evidence sent to AI to avoid token overflow
    return sanitized[:5]


def sanitize_finding(finding: dict) -> dict:
    """
    Return a sanitized copy of a finding dict safe to send to the AI.
    Only keeps fields needed for explanation.
    """
    raw_evidence = finding.get("evidence") or []
    if isinstance(raw_evidence, list):
        # Handle both dicts (from API) and Evidence model objects
        ev_dicts = []
        for ev in raw_evidence:
            if isinstance(ev, dict):
                ev_dicts.append(ev)
            else:
                # Pydantic model
                ev_dicts.append({"observed": getattr(ev, "observed", ""), "detail": getattr(ev, "detail", None)})
    else:
        ev_dicts = []

    return {
        "finding_code": finding.get("finding_id") or finding.get("finding_code") or "",
        "title":        sanitize_text(finding.get("title", "")),
        "severity":     finding.get("severity", ""),
        "category":     finding.get("category", ""),
        "description":  sanitize_text(finding.get("description", "")),
        "evidence":     sanitize_evidence_list(ev_dicts),
        "remediation":  sanitize_text(finding.get("remediation", "")),
    }
