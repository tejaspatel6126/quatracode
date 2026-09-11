"""
Finding Rule Registry — Phase 05.

A central, immutable registry mapping observation conditions to finding
definitions (finding_id, title, description, severity, remediation).

RULES:
  - All severity values come from SCANNER_SPECIFICATION.md — not invented here.
  - No user-controlled severity accepted anywhere in this file.
  - Finding IDs must not be renamed after shipping.
  - No AI, no probabilistic logic.
  - Same conditions → same finding, always.
"""

from dataclasses import dataclass

from app.findings.models import FindingCategory, FindingId, Severity


# ── Rule definition ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FindingRule:
    finding_id:  str
    check_id:    str           # Phase 04 CheckId constant
    category:    FindingCategory
    title:       str
    description: str
    severity:    Severity
    confidence:  float
    remediation: str
    references:  tuple[str, ...] = ()
    rule_version: str = "1.0"


# ── Registry ──────────────────────────────────────────────────────────────────
# Keyed by finding_id for fast lookup. Values are immutable FindingRule objects.

RULE_REGISTRY: dict[str, FindingRule] = {

    # ── TLS Protocol (SCANNER_SPECIFICATION.md §14) ─────────────────────────

    FindingId.TLS_1_0_ENABLED: FindingRule(
        finding_id  = FindingId.TLS_1_0_ENABLED,
        check_id    = "TLS_PROTOCOL",
        category    = FindingCategory.TLS,
        title       = "Deprecated TLS 1.0 Supported",
        description = (
            "The server accepts TLS 1.0, a protocol deprecated in 2020 (RFC 8996). "
            "TLS 1.0 has known weaknesses (BEAST, POODLE variants) and should be "
            "disabled in favour of TLS 1.2 or higher."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Disable TLS 1.0 on the server. Configure a minimum of TLS 1.2 "
            "(TLS 1.3 preferred). Update cipher suite configuration accordingly."
        ),
        references  = (
            "https://datatracker.ietf.org/doc/html/rfc8996",
            "https://owasp.org/www-project-transport-layer-protection/",
        ),
    ),

    FindingId.TLS_1_1_ENABLED: FindingRule(
        finding_id  = FindingId.TLS_1_1_ENABLED,
        check_id    = "TLS_PROTOCOL",
        category    = FindingCategory.TLS,
        title       = "Deprecated TLS 1.1 Supported",
        description = (
            "The server accepts TLS 1.1, a protocol deprecated in 2020 (RFC 8996). "
            "TLS 1.1 is considered insufficient for modern transport security."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Disable TLS 1.1 on the server. Configure a minimum of TLS 1.2 "
            "(TLS 1.3 preferred)."
        ),
        references  = (
            "https://datatracker.ietf.org/doc/html/rfc8996",
        ),
    ),

    # ── Certificate (§8, §9, §10, §11) ──────────────────────────────────────

    FindingId.TLS_CERT_EXPIRED: FindingRule(
        finding_id  = FindingId.TLS_CERT_EXPIRED,
        check_id    = "TLS_CERT_EXPIRY",
        category    = FindingCategory.CERTIFICATE,
        title       = "TLS Certificate Expired",
        description = (
            "The TLS certificate presented by the server has passed its "
            "notAfter validity date. Browsers will reject the connection with "
            "a certificate error, causing service disruption."
        ),
        severity    = Severity.CRITICAL,
        confidence  = 1.0,
        remediation = (
            "Renew the TLS certificate immediately. Implement automated "
            "certificate renewal (e.g. Let's Encrypt with ACME) to prevent "
            "future expiry."
        ),
        references  = (
            "https://datatracker.ietf.org/doc/html/rfc5280",
        ),
    ),

    FindingId.TLS_CERT_EXPIRY_SOON_HIGH: FindingRule(
        finding_id  = FindingId.TLS_CERT_EXPIRY_SOON_HIGH,
        check_id    = "TLS_CERT_EXPIRY",
        category    = FindingCategory.CERTIFICATE,
        title       = "TLS Certificate Expiring Very Soon (1–6 Days)",
        description = (
            "The TLS certificate will expire within 6 days. "
            "Immediate action is required to prevent a certificate error."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Renew the TLS certificate immediately before it expires."
        ),
        references  = ("https://datatracker.ietf.org/doc/html/rfc5280",),
    ),

    FindingId.TLS_CERT_EXPIRY_SOON_MEDIUM: FindingRule(
        finding_id  = FindingId.TLS_CERT_EXPIRY_SOON_MEDIUM,
        check_id    = "TLS_CERT_EXPIRY",
        category    = FindingCategory.CERTIFICATE,
        title       = "TLS Certificate Expiring Soon (7–14 Days)",
        description = (
            "The TLS certificate will expire within 14 days. "
            "Renew the certificate promptly."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = "Renew the TLS certificate before it expires.",
        references  = ("https://datatracker.ietf.org/doc/html/rfc5280",),
    ),

    FindingId.TLS_CERT_EXPIRY_SOON_LOW: FindingRule(
        finding_id  = FindingId.TLS_CERT_EXPIRY_SOON_LOW,
        check_id    = "TLS_CERT_EXPIRY",
        category    = FindingCategory.CERTIFICATE,
        title       = "TLS Certificate Expiring (15–30 Days)",
        description = (
            "The TLS certificate will expire within 30 days. "
            "Plan for renewal to avoid service disruption."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = "Schedule TLS certificate renewal within the next 2 weeks.",
        references  = ("https://datatracker.ietf.org/doc/html/rfc5280",),
    ),

    FindingId.TLS_CERT_HOSTNAME_MISMATCH: FindingRule(
        finding_id  = FindingId.TLS_CERT_HOSTNAME_MISMATCH,
        check_id    = "TLS_CERT_HOSTNAME",
        category    = FindingCategory.CERTIFICATE,
        title       = "Certificate Hostname Mismatch",
        description = (
            "The TLS certificate presented does not cover the requested hostname. "
            "This causes browsers to display a certificate error and prevents "
            "secure connections from being established."
        ),
        severity    = Severity.CRITICAL,
        confidence  = 1.0,
        remediation = (
            "Obtain a certificate that covers the correct hostname(s) via SAN entries. "
            "Ensure the certificate is deployed on the correct virtual host."
        ),
        references  = (
            "https://datatracker.ietf.org/doc/html/rfc2818",
            "https://owasp.org/www-project-transport-layer-protection/",
        ),
    ),

    FindingId.TLS_CERT_SELF_SIGNED: FindingRule(
        finding_id  = FindingId.TLS_CERT_SELF_SIGNED,
        check_id    = "TLS_CERT_SELF_SIGNED",
        category    = FindingCategory.CERTIFICATE,
        title       = "Self-Signed TLS Certificate",
        description = (
            "The TLS certificate is self-signed and not issued by a trusted "
            "Certificate Authority. Browsers will display a certificate warning, "
            "and the connection is not trusted by default."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Replace the self-signed certificate with one issued by a trusted "
            "Certificate Authority. Free certificates are available from "
            "Let's Encrypt."
        ),
        references  = ("https://letsencrypt.org/",),
    ),

    # ── HTTP Headers (§17–23) ────────────────────────────────────────────────

    FindingId.HTTP_HSTS_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_HSTS_MISSING,
        check_id    = "HTTP_HSTS",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing Strict-Transport-Security Header",
        description = (
            "The Strict-Transport-Security (HSTS) response header is absent. "
            "Without HSTS, browsers are not instructed to use HTTPS exclusively, "
            "leaving the site vulnerable to SSL stripping attacks."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' "
            "to all HTTPS responses after confirming HTTPS is correctly deployed."
        ),
        references  = (
            "https://owasp.org/www-project-secure-headers/",
            "https://datatracker.ietf.org/doc/html/rfc6797",
        ),
    ),

    FindingId.HTTP_HSTS_SHORT_MAX_AGE: FindingRule(
        finding_id  = FindingId.HTTP_HSTS_SHORT_MAX_AGE,
        check_id    = "HTTP_HSTS",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "HSTS max-age Too Short",
        description = (
            "The Strict-Transport-Security header is present but specifies a "
            "max-age below the recommended minimum. A short max-age limits the "
            "effectiveness of the HSTS policy."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Set max-age to at least 31536000 seconds (1 year). "
            "Consider adding includeSubDomains and preload for stronger protection."
        ),
        references  = ("https://datatracker.ietf.org/doc/html/rfc6797",),
    ),

    FindingId.HTTP_CSP_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_CSP_MISSING,
        check_id    = "HTTP_CSP",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing Content-Security-Policy Header",
        description = (
            "The Content-Security-Policy response header is absent. "
            "CSP reduces the risk of XSS attacks by controlling which resources "
            "the browser is allowed to load."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Implement a Content-Security-Policy header. Start with a restrictive "
            "policy such as \"default-src 'self'\" and extend as needed."
        ),
        references  = (
            "https://owasp.org/www-project-secure-headers/",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",
        ),
    ),

    FindingId.HTTP_CSP_UNSAFE_INLINE: FindingRule(
        finding_id  = FindingId.HTTP_CSP_UNSAFE_INLINE,
        check_id    = "HTTP_CSP",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "CSP Allows Unsafe Inline Scripts",
        description = (
            "The Content-Security-Policy includes 'unsafe-inline', which permits "
            "inline JavaScript execution. This significantly reduces the effectiveness "
            "of the policy against XSS attacks."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Remove 'unsafe-inline' from the CSP. Use nonces or hashes for "
            "legitimate inline scripts."
        ),
        references  = ("https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",),
    ),

    FindingId.HTTP_CSP_UNSAFE_EVAL: FindingRule(
        finding_id  = FindingId.HTTP_CSP_UNSAFE_EVAL,
        check_id    = "HTTP_CSP",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "CSP Allows Unsafe Eval",
        description = (
            "The Content-Security-Policy includes 'unsafe-eval', which permits "
            "dynamic JavaScript execution via eval(). This reduces XSS protection."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Remove 'unsafe-eval' from the CSP. Refactor application code to "
            "avoid eval() and similar dynamic execution patterns."
        ),
        references  = ("https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",),
    ),

    FindingId.HTTP_X_CONTENT_TYPE_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_X_CONTENT_TYPE_MISSING,
        check_id    = "HTTP_X_CONTENT_TYPE_OPTIONS",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing X-Content-Type-Options Header",
        description = (
            "The X-Content-Type-Options response header is absent. "
            "Without 'nosniff', browsers may interpret files with incorrect MIME types, "
            "potentially enabling MIME-type sniffing attacks."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Add 'X-Content-Type-Options: nosniff' to all HTTP responses."
        ),
        references  = ("https://owasp.org/www-project-secure-headers/",),
    ),

    FindingId.HTTP_FRAME_PROTECTION_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_FRAME_PROTECTION_MISSING,
        check_id    = "HTTP_FRAME_PROTECTION",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing Clickjacking Protection",
        description = (
            "Neither X-Frame-Options nor Content-Security-Policy frame-ancestors "
            "is configured. Without frame protection, the page may be embedded in "
            "an iframe on a malicious site (clickjacking)."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Add 'X-Frame-Options: DENY' or include 'frame-ancestors' in "
            "Content-Security-Policy."
        ),
        references  = (
            "https://owasp.org/www-community/attacks/Clickjacking",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options",
        ),
    ),

    FindingId.HTTP_REFERRER_POLICY_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_REFERRER_POLICY_MISSING,
        check_id    = "HTTP_REFERRER_POLICY",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing Referrer-Policy Header",
        description = (
            "The Referrer-Policy header is absent. Without it, the browser "
            "may send full URL referrer information to third parties, "
            "potentially leaking sensitive URL parameters."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Add 'Referrer-Policy: strict-origin-when-cross-origin' "
            "or 'no-referrer' to HTTP responses."
        ),
        references  = (
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy",
        ),
    ),

    FindingId.HTTP_REFERRER_POLICY_WEAK: FindingRule(
        finding_id  = FindingId.HTTP_REFERRER_POLICY_WEAK,
        check_id    = "HTTP_REFERRER_POLICY",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Weak Referrer-Policy",
        description = (
            "The Referrer-Policy header is set to 'unsafe-url', which causes "
            "full URL referrer information to be sent to all destinations, "
            "including cross-origin requests."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Replace 'unsafe-url' with a more restrictive policy such as "
            "'strict-origin-when-cross-origin' or 'no-referrer'."
        ),
        references  = (
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy",
        ),
    ),

    FindingId.HTTP_PERMISSIONS_POLICY_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_PERMISSIONS_POLICY_MISSING,
        check_id    = "HTTP_PERMISSIONS_POLICY",
        category    = FindingCategory.HTTP_HEADERS,
        title       = "Missing Permissions-Policy Header",
        description = (
            "The Permissions-Policy header is absent. This header controls "
            "access to browser features (camera, microphone, geolocation). "
            "Without it, all features are allowed by default."
        ),
        severity    = Severity.LOW,
        confidence  = 1.0,
        remediation = (
            "Add a Permissions-Policy header restricting unneeded browser "
            "features, e.g. 'Permissions-Policy: camera=(), microphone=()'."
        ),
        references  = (
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy",
        ),
    ),

    # ── Cookies (§26–28) ────────────────────────────────────────────────────

    FindingId.HTTP_COOKIE_SECURE_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_COOKIE_SECURE_MISSING,
        check_id    = "HTTP_COOKIE_SECURITY",
        category    = FindingCategory.COOKIES,
        title       = "Cookie Missing Secure Attribute",
        description = (
            "One or more cookies are set without the Secure attribute over "
            "an HTTPS session. Without Secure, cookies may be transmitted "
            "over unencrypted HTTP connections."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Set the Secure attribute on all cookies that contain sensitive data. "
            "Example: Set-Cookie: id=abc; Secure; HttpOnly"
        ),
        references  = (
            "https://owasp.org/www-community/controls/SecureCookieAttribute",
        ),
    ),

    FindingId.HTTP_COOKIE_HTTPONLY_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_COOKIE_HTTPONLY_MISSING,
        check_id    = "HTTP_COOKIE_SECURITY",
        category    = FindingCategory.COOKIES,
        title       = "Cookie Missing HttpOnly Attribute",
        description = (
            "One or more cookies lack the HttpOnly attribute. Without HttpOnly, "
            "JavaScript can access cookie values, increasing the impact of "
            "cross-site scripting (XSS) attacks."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Set the HttpOnly attribute on all cookies that do not need "
            "to be accessed by client-side JavaScript."
        ),
        references  = (
            "https://owasp.org/www-community/HttpOnly",
        ),
    ),

    FindingId.HTTP_COOKIE_SAMESITE_NONE_INSECURE: FindingRule(
        finding_id  = FindingId.HTTP_COOKIE_SAMESITE_NONE_INSECURE,
        check_id    = "HTTP_COOKIE_SECURITY",
        category    = FindingCategory.COOKIES,
        title       = "Cookie SameSite=None Without Secure",
        description = (
            "A cookie is set with SameSite=None but without the Secure attribute. "
            "Modern browsers require Secure when SameSite=None is used, and may "
            "reject the cookie entirely."
        ),
        severity    = Severity.MEDIUM,
        confidence  = 1.0,
        remediation = (
            "Add the Secure attribute to all cookies using SameSite=None, "
            "or use SameSite=Lax/Strict instead."
        ),
        references  = (
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite",
        ),
    ),

    # ── Redirects (§31–32) ───────────────────────────────────────────────────

    FindingId.HTTP_HTTPS_REDIRECT_MISSING: FindingRule(
        finding_id  = FindingId.HTTP_HTTPS_REDIRECT_MISSING,
        check_id    = "HTTP_HTTPS_REDIRECT",
        category    = FindingCategory.REDIRECTS,
        title       = "HTTP Does Not Redirect to HTTPS",
        description = (
            "The HTTP endpoint does not redirect to HTTPS. Users accessing "
            "the site over HTTP will not be automatically upgraded to a "
            "secure connection, leaving their traffic unencrypted."
        ),
        severity    = Severity.HIGH,
        confidence  = 1.0,
        remediation = (
            "Configure the web server to redirect all HTTP traffic to HTTPS "
            "using a permanent redirect (HTTP 301 or 308). "
            "Then enable HSTS to prevent future plain-HTTP access."
        ),
        references  = (
            "https://owasp.org/www-project-transport-layer-protection/",
        ),
    ),
}


def get_rule(finding_id: str) -> FindingRule | None:
    """Return the rule for a finding_id, or None if not registered."""
    return RULE_REGISTRY.get(finding_id)


def all_rules() -> list[FindingRule]:
    """Return all registered rules in deterministic order."""
    return [RULE_REGISTRY[k] for k in sorted(RULE_REGISTRY.keys())]
