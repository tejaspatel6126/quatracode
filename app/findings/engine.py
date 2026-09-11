"""
Finding Engine — Phase 05.

Converts Phase 04 ScanResult observations into SecurityFindings.

Design rules:
  - Deterministic: same observations → same findings, always.
  - No AI, no probabilistic logic.
  - No user-controlled severity.
  - Deduplication by finding_id: one finding per unique finding_id.
  - Evidence must be security-safe (no credentials, no cookie values).
  - No network requests.

Pipeline:
    ScanResult  →  [rules per module]  →  [deduplicate]  →  list[SecurityFinding]
"""

from __future__ import annotations

import logging

from app.findings.models import (
    Evidence,
    FindingId,
    SecurityFinding,
    Severity,
)
from app.findings.registry import RULE_REGISTRY, FindingRule
from app.schemas.scan_result import (
    CertHostnameState,
    CertValidityState,
    ScanResult,
    TLSVersion,
)

logger = logging.getLogger(__name__)

# HSTS max-age threshold below which we report SHORT_MAX_AGE (§18)
_HSTS_MIN_MAX_AGE = 86400  # 1 day — short max-age is a hardening issue

# Referrer-Policy values considered "weak" (§22)
_WEAK_REFERRER_POLICIES: frozenset[str] = frozenset({"unsafe-url"})

# Referrer-Policy values considered acceptable (§22)
_GOOD_REFERRER_POLICIES: frozenset[str] = frozenset({
    "no-referrer",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "same-origin",
    "origin",
})


class FindingEngine:
    """
    Converts a Phase 04 ScanResult into a deduplicated list of SecurityFindings.

    Instantiate once; call run(scan_result) per scan.
    """

    def run(self, scan_result: ScanResult) -> list[SecurityFinding]:
        """
        Main entry point.

        Parameters
        ----------
        scan_result : ScanResult
            Phase 04 raw observations.

        Returns
        -------
        list[SecurityFinding]
            Deduplicated, ordered (CRITICAL → INFO) list of findings.
            Empty list if scan is clean or unavailable.
        """
        findings: dict[str, SecurityFinding] = {}  # keyed by finding_id (dedup)

        self._check_tls(scan_result, findings)
        self._check_certificate(scan_result, findings)
        self._check_headers(scan_result, findings)
        self._check_cookies(scan_result, findings)
        self._check_redirects(scan_result, findings)
        # Nmap observations: no findings defined in spec for port discovery alone.
        # Future rules may be added here when documented.

        result = list(findings.values())
        result.sort(key=lambda f: (-_severity_order(f.severity), f.finding_id))
        logger.info("Finding engine: %d findings from scan of %s", len(result), scan_result.target_hostname)
        return result

    # ── TLS protocol ──────────────────────────────────────────────────────────

    def _check_tls(self, scan: ScanResult, out: dict[str, SecurityFinding]) -> None:
        if scan.tls is None or not scan.tls.available:
            return

        tls = scan.tls

        if tls.tls_1_0:
            _emit(out, FindingId.TLS_1_0_ENABLED, [
                Evidence(observed="TLS 1.0 protocol is accepted by the server."),
            ])

        if tls.tls_1_1:
            _emit(out, FindingId.TLS_1_1_ENABLED, [
                Evidence(observed="TLS 1.1 protocol is accepted by the server."),
            ])

    # ── Certificate ───────────────────────────────────────────────────────────

    def _check_certificate(self, scan: ScanResult, out: dict[str, SecurityFinding]) -> None:
        if scan.certificate is None or not scan.certificate.available:
            return

        cert = scan.certificate

        # Expired (CRITICAL) — overrides all expiry-soon findings
        if cert.validity_state == CertValidityState.EXPIRED:
            days = cert.days_until_expiry or 0
            _emit(out, FindingId.TLS_CERT_EXPIRED, [
                Evidence(
                    observed="TLS certificate is expired.",
                    detail=f"Certificate expired {abs(days)} day(s) ago.",
                ),
            ])
        elif cert.validity_state == CertValidityState.VALID and cert.days_until_expiry is not None:
            days = cert.days_until_expiry
            if 1 <= days <= 6:
                _emit(out, FindingId.TLS_CERT_EXPIRY_SOON_HIGH, [
                    Evidence(observed=f"Certificate expires in {days} day(s)."),
                ])
            elif 7 <= days <= 14:
                _emit(out, FindingId.TLS_CERT_EXPIRY_SOON_MEDIUM, [
                    Evidence(observed=f"Certificate expires in {days} day(s)."),
                ])
            elif 15 <= days <= 30:
                _emit(out, FindingId.TLS_CERT_EXPIRY_SOON_LOW, [
                    Evidence(observed=f"Certificate expires in {days} day(s)."),
                ])

        # Hostname mismatch (CRITICAL)
        if cert.hostname_validation == CertHostnameState.MISMATCH:
            _emit(out, FindingId.TLS_CERT_HOSTNAME_MISMATCH, [
                Evidence(
                    observed="Certificate hostname does not match the target.",
                    detail=f"Target hostname: {scan.target_hostname}",
                ),
            ])

        # Self-signed (HIGH)
        if cert.is_self_signed:
            issuer_cn = (cert.issuer or {}).get("commonName", "unknown")
            _emit(out, FindingId.TLS_CERT_SELF_SIGNED, [
                Evidence(
                    observed="Certificate is self-signed.",
                    detail=f"Issuer: {issuer_cn}",
                ),
            ])

    # ── HTTP Headers ──────────────────────────────────────────────────────────

    def _check_headers(self, scan: ScanResult, out: dict[str, SecurityFinding]) -> None:
        if scan.headers is None or not scan.headers.available:
            return

        h = scan.headers

        # HSTS — only check for HTTPS targets (§17.1)
        if scan.target_scheme == "https":
            if not h.hsts.present:
                _emit(out, FindingId.HTTP_HSTS_MISSING, [
                    Evidence(observed="Strict-Transport-Security header is absent."),
                ])
            elif h.hsts.max_age is not None and h.hsts.max_age < _HSTS_MIN_MAX_AGE:
                _emit(out, FindingId.HTTP_HSTS_SHORT_MAX_AGE, [
                    Evidence(
                        observed="HSTS max-age is below the recommended minimum.",
                        detail=f"Observed max-age: {h.hsts.max_age}s (minimum recommended: {_HSTS_MIN_MAX_AGE}s)",
                    ),
                ])

        # CSP
        if not h.csp.present:
            _emit(out, FindingId.HTTP_CSP_MISSING, [
                Evidence(observed="Content-Security-Policy header is absent."),
            ])
        else:
            directives = set(h.csp.directive_names)
            if "'unsafe-inline'" in (h.csp.raw_value or ""):
                _emit(out, FindingId.HTTP_CSP_UNSAFE_INLINE, [
                    Evidence(observed="CSP contains 'unsafe-inline' directive."),
                ])
            if "'unsafe-eval'" in (h.csp.raw_value or ""):
                _emit(out, FindingId.HTTP_CSP_UNSAFE_EVAL, [
                    Evidence(observed="CSP contains 'unsafe-eval' directive."),
                ])

        # X-Content-Type-Options
        xcto = h.x_content_type_options
        if not xcto.present or xcto.normalized_value != "nosniff":
            _emit(out, FindingId.HTTP_X_CONTENT_TYPE_MISSING, [
                Evidence(
                    observed="X-Content-Type-Options header is absent or not set to 'nosniff'.",
                    detail=f"Observed value: {xcto.raw_value!r}" if xcto.present else None,
                ),
            ])

        # Frame protection
        fp = h.frame_protection
        if not fp.x_frame_options_present and not fp.csp_frame_ancestors_present:
            _emit(out, FindingId.HTTP_FRAME_PROTECTION_MISSING, [
                Evidence(
                    observed="Neither X-Frame-Options nor CSP frame-ancestors is configured.",
                ),
            ])

        # Referrer-Policy
        rp = h.referrer_policy
        if not rp.present:
            _emit(out, FindingId.HTTP_REFERRER_POLICY_MISSING, [
                Evidence(observed="Referrer-Policy header is absent."),
            ])
        elif rp.normalized_value in _WEAK_REFERRER_POLICIES:
            _emit(out, FindingId.HTTP_REFERRER_POLICY_WEAK, [
                Evidence(
                    observed=f"Referrer-Policy is set to a weak value: '{rp.normalized_value}'.",
                ),
            ])

        # Permissions-Policy
        if not h.permissions_policy.present:
            _emit(out, FindingId.HTTP_PERMISSIONS_POLICY_MISSING, [
                Evidence(observed="Permissions-Policy header is absent."),
            ])

    # ── Cookies ───────────────────────────────────────────────────────────────

    def _check_cookies(self, scan: ScanResult, out: dict[str, SecurityFinding]) -> None:
        if scan.cookies is None or not scan.cookies.available:
            return

        cookies = scan.cookies.cookies
        if not cookies:
            return

        # Collect cookie names for evidence (safe — values always redacted)
        insecure_secure  = [c.name for c in cookies if not c.secure]
        insecure_httponly = [c.name for c in cookies if not c.http_only]
        samesite_none_insecure = [
            c.name for c in cookies
            if c.same_site and c.same_site.lower() == "none" and not c.secure
        ]

        # Only emit for HTTPS targets (Secure attribute is only meaningful on HTTPS)
        if scan.target_scheme == "https" and insecure_secure:
            names_str = ", ".join(insecure_secure[:5])  # cap evidence length
            _emit(out, FindingId.HTTP_COOKIE_SECURE_MISSING, [
                Evidence(
                    observed=f"{len(insecure_secure)} cookie(s) lack the Secure attribute.",
                    detail=f"Cookie names: {names_str}",
                ),
            ])

        if insecure_httponly:
            names_str = ", ".join(insecure_httponly[:5])
            _emit(out, FindingId.HTTP_COOKIE_HTTPONLY_MISSING, [
                Evidence(
                    observed=f"{len(insecure_httponly)} cookie(s) lack the HttpOnly attribute.",
                    detail=f"Cookie names: {names_str}",
                ),
            ])

        if samesite_none_insecure:
            names_str = ", ".join(samesite_none_insecure[:5])
            _emit(out, FindingId.HTTP_COOKIE_SAMESITE_NONE_INSECURE, [
                Evidence(
                    observed=f"{len(samesite_none_insecure)} cookie(s) use SameSite=None without Secure.",
                    detail=f"Cookie names: {names_str}",
                ),
            ])

    # ── Redirects ─────────────────────────────────────────────────────────────

    def _check_redirects(self, scan: ScanResult, out: dict[str, SecurityFinding]) -> None:
        if scan.redirects is None or not scan.redirects.available:
            return

        r = scan.redirects
        # Only emit if we started from HTTP and no redirect to HTTPS was observed
        if scan.target_scheme == "http" and not r.https_redirect_observed:
            _emit(out, FindingId.HTTP_HTTPS_REDIRECT_MISSING, [
                Evidence(
                    observed="HTTP endpoint does not redirect to HTTPS.",
                    detail=f"Final URL: {r.final_url}",
                ),
            ])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _emit(
    out: dict[str, SecurityFinding],
    finding_id: str,
    evidence: list[Evidence],
) -> None:
    """
    Create a SecurityFinding from the registry and add to out (dedup by finding_id).
    If finding_id already present, skip (deduplication).
    """
    if finding_id in out:
        return  # already emitted — no duplicates

    rule = RULE_REGISTRY.get(finding_id)
    if rule is None:
        logger.warning("Finding engine: no rule registered for %r — skipping", finding_id)
        return

    out[finding_id] = SecurityFinding(
        finding_id   = rule.finding_id,
        check_id     = rule.check_id,
        category     = rule.category,
        title        = rule.title,
        description  = rule.description,
        severity     = rule.severity,
        confidence   = rule.confidence,
        evidence     = evidence,
        remediation  = rule.remediation,
        references   = list(rule.references),
        rule_version = rule.rule_version,
    )


_SEVERITY_ORDER_MAP: dict[Severity, int] = {
    Severity.INFO:     0,
    Severity.LOW:      1,
    Severity.MEDIUM:   2,
    Severity.HIGH:     3,
    Severity.CRITICAL: 4,
}


def _severity_order(s: Severity) -> int:
    return _SEVERITY_ORDER_MAP.get(s, 0)
