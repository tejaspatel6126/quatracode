# AI-Powered Web Security Configuration Auditor

## Scanner Specification

**Version:** 1.0
**Project Type:** Hackathon Project
**Domain:** Cybersecurity & Data Protection
**Problem Statement:** Problem 4.3 — Hidden SSL/TLS and Web Security Configuration Weaknesses
**Status:** Initial / Development Baseline

---

## 1. Purpose

This document defines the technical behavior of every security scanner implemented by the AI-Powered Web Security Configuration Auditor.

It specifies:

- What each scanner checks
- How the check is performed
- What evidence is collected
- How findings are generated
- Severity rules
- Confidence rules
- Remediation guidance
- Failure behavior
- Safety restrictions

The scanner specification is the technical source of truth for security detection logic.

AI-generated explanations must never override these deterministic rules.

---

## 2. Scanner Architecture

The system consists of the following scanners:

```
                    SCAN TARGET
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
     TLS Scanner    HTTP Scanner   Content Scanner
          |              |              |
          |         +----+----+         |
          |         |         |         |
          |         v         v         v
          |      Headers    Cookies   Resources
          |         |         |         |
          +---------+---------+---------+
                    |
                    v
              Finding Engine
                    |
                    v
               Risk Engine
```

Initial scanners:

- TLS Scanner
- Security Header Scanner
- Cookie Scanner
- Redirect Scanner
- Content Scanner
- Resource Scanner

---

## 3. Common Scanner Contract

Every scanner should follow a common conceptual interface.

```python
class BaseScanner:

    async def scan(self, target):
        """
        Perform a controlled security assessment
        and return structured results.
        """
        raise NotImplementedError
```

A scanner should return structured data.

Example:

```json
{
  "scanner": "tls",
  "status": "completed",
  "data": {},
  "findings": []
}
```

---

## 4. Scanner Safety Rules

All scanners must follow these rules.

### 4.1 No Exploitation

The scanners must not:

- Exploit vulnerabilities
- Attempt credential attacks
- Perform brute force
- Attempt authentication bypass
- Execute arbitrary payloads
- Modify target data
- Upload files
- Submit destructive requests

### 4.2 Request Limits

Every scanner must use:

- Connection timeout
- Read timeout
- Maximum response size
- Maximum redirects
- Maximum analyzed resources
- Bounded concurrency

### 4.3 Safe HTTP Methods

The default assessment should use:

- `GET`
- `HEAD`

where appropriate.

The scanner must not use:

- `POST`
- `PUT`
- `PATCH`
- `DELETE`

unless a future explicitly authorized feature requires it.

### 4.4 Redirect Safety

Every redirect destination must be validated again.

Example:

```
Target
  |
  v
Redirect
  |
  v
Validate Destination
  |
  v
Continue
```

The scanner must not follow redirects into unsafe internal destinations.

---

## 5. Target Normalization

Before scanning, the URL must be normalized.

Example: `https://example.com/`

should become a normalized target representation containing:

- scheme
- hostname
- port
- path

The scanner must reject:

- Invalid URLs
- Unsupported protocols
- Missing hostnames
- Clearly unsafe destinations

Supported schemes:

- `http`
- `https`

---

## 6. TLS Scanner

### 6.1 Purpose

The TLS Scanner evaluates publicly observable TLS certificate and protocol configuration.

Primary implementation technologies:

- Python `ssl`
- Python `socket`
- `cryptography`

---

## 7. TLS Certificate Checks

The TLS Scanner should inspect:

- Certificate validity
- Certificate expiration
- Certificate issuer
- Certificate subject
- SAN entries
- Hostname match
- Self-signed status
- Certificate chain validity where observable

---

## 8. Certificate Validity

The scanner shall determine whether the certificate is currently valid.

**PASS** — Certificate is within its validity period.

**CRITICAL** — Certificate is expired.

Example:

```
Certificate expired.

Severity: CRITICAL
Confidence: HIGH
```

---

## 9. Certificate Expiration Warning

The scanner should report upcoming expiration.

Suggested thresholds:

| Days Remaining | Severity |
|---|---|
| > 30 days | PASS |
| 15 - 30 days | LOW |
| 7 - 14 days | MEDIUM |
| 1 - 6 days | HIGH |
| Expired | CRITICAL |

The exact threshold values may be adjusted during testing.

---

## 10. Hostname Validation

The scanner must verify whether the certificate covers the requested hostname.

Sources may include:

- Subject Alternative Name
- Certificate hostname matching rules

**PASS** — Hostname is covered.

**CRITICAL** — Certificate does not match the requested hostname.

Example:

```
Target:
example.com

Certificate:
other-domain.com

Finding:
Certificate hostname mismatch

Severity:
CRITICAL
```

---

## 11. Self-Signed Certificate

The scanner should identify self-signed certificates.

A self-signed certificate should normally be classified as **Severity: HIGH**.

However, the finding may require contextual interpretation because internal development environments may intentionally use self-signed certificates.

The report should clearly state that the certificate is not trusted by normal public certificate trust chains.

---

## 12. Certificate Chain

Where technically observable, the scanner should evaluate whether the certificate chain can be validated.

Potential findings:

- Incomplete certificate chain
- Invalid certificate chain
- Untrusted certificate chain

Suggested severity:

- Invalid / unusable chain — **HIGH**
- Incomplete chain affecting client validation — **HIGH**

If chain information cannot be reliably determined, the scanner must report:

```
Unable to fully assess certificate chain.
```

It must not invent a failure.

---

## 13. TLS Protocol Scanner

The TLS Scanner should determine which TLS protocol versions can be successfully negotiated where technically possible.

Initial protocol set:

- TLS 1.0
- TLS 1.1
- TLS 1.2
- TLS 1.3

---

## 14. Deprecated TLS Versions

**TLS 1.0** — If supported: **Severity: HIGH**

```
Deprecated TLS 1.0 protocol is supported.
```

**TLS 1.1** — If supported: **Severity: HIGH**

```
Deprecated TLS 1.1 protocol is supported.
```

**TLS 1.2** — Considered an accepted modern protocol. Presence: **PASS**

**TLS 1.3** — Preferred when available.

Absence of TLS 1.3 alone should not automatically be classified as a vulnerability because TLS 1.2 can still provide an acceptable configuration.

---

## 15. TLS Protocol Summary

Example:

```json
{
  "tls_1_0": false,
  "tls_1_1": false,
  "tls_1_2": true,
  "tls_1_3": true
}
```

Example report:

```
TLS 1.0     Disabled
TLS 1.1     Disabled
TLS 1.2     Enabled
TLS 1.3     Enabled

Status:
GOOD
```

---

## 16. Security Header Scanner

### 16.1 Purpose

The Security Header Scanner evaluates important HTTP response security headers.

Initial headers:

- Strict-Transport-Security
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy

---

## 17. HSTS Check

Header: `Strict-Transport-Security`

The scanner checks:

- Presence
- Basic directive validity
- `max-age`
- `includeSubDomains`
- `preload` where present

### 17.1 Missing HSTS

If HTTPS is successfully available but HSTS is absent:

**Severity: HIGH**

Finding:

```
Strict-Transport-Security header is missing.
```

Recommendation:

```
Configure an appropriate HSTS policy after
confirming that HTTPS is correctly deployed.
```

---

## 18. HSTS max-age

The scanner should inspect the `max-age` directive.

Very short policies may be reported as a hardening issue rather than automatically classified as a vulnerability.

The scanner must avoid treating every unusual HSTS value as a critical security failure.

---

## 19. Content-Security-Policy

Header: `Content-Security-Policy`

The scanner checks:

- Presence
- Basic directive structure
- Potentially unsafe broad directives

Examples requiring review:

- `*`
- `'unsafe-inline'`
- `'unsafe-eval'`

A weak CSP should generally be: **Severity: MEDIUM**

Missing CSP: **Severity: MEDIUM**

The scanner should avoid claiming that a missing CSP automatically means XSS is exploitable.

---

## 20. X-Content-Type-Options

Expected secure value: `nosniff`

If missing: **Severity: LOW**

If present with `nosniff`: **PASS**

---

## 21. X-Frame-Options

Accepted values include:

- `DENY`
- `SAMEORIGIN`

If missing: **Severity: LOW**

If an invalid or unexpected value is observed: **Severity: LOW**

The report should explain that clickjacking protection may be weaker.

---

## 22. Referrer-Policy

The scanner should inspect: `Referrer-Policy`

Recommended values include privacy-conscious policies such as:

- `no-referrer`
- `strict-origin`
- `strict-origin-when-cross-origin`
- `same-origin`

Missing or weak configuration: **Severity: LOW**

The scanner should distinguish between:

- Missing
- Weak
- Acceptable

---

## 23. Permissions-Policy

The scanner should detect: `Permissions-Policy`

Missing policy: **Severity: LOW**

The absence should be treated as a hardening opportunity unless specific evidence indicates greater risk.

---

## 24. Header Evidence

Every header result should store:

```json
{
  "header_name": "Strict-Transport-Security",
  "present": false,
  "header_value": null,
  "evaluation": "missing"
}
```

The exact observed value should be retained where appropriate.

---

## 25. Cookie Scanner

### 25.1 Purpose

The Cookie Scanner analyzes publicly observable `Set-Cookie` headers.

The scanner checks:

- Secure
- HttpOnly
- SameSite
- Domain
- Path
- Expires
- Max-Age

---

## 26. Secure Attribute

If a cookie appears to be transmitted without the `Secure` attribute over an HTTPS session:

**Severity: MEDIUM**

However, context must be considered.

The scanner must not automatically classify every cookie without `Secure` as a critical session vulnerability.

---

## 27. HttpOnly Attribute

If a cookie appears to represent a session/authentication cookie and lacks `HttpOnly`:

**Severity: MEDIUM**

The scanner should use conservative classification when cookie purpose cannot be established.

Example:

```
Cookie:
session_id

HttpOnly:
Missing

Severity:
MEDIUM
```

---

## 28. SameSite Attribute

The scanner should inspect:

- `SameSite=Strict`
- `SameSite=Lax`
- `SameSite=None`

If `SameSite=None`, the scanner should verify whether `Secure` is also present.

An insecure combination should generate a finding.

---

## 29. Cookie Evidence

Example:

```json
{
  "cookie_name": "session_id",
  "secure": false,
  "http_only": false,
  "same_site": null
}
```

The report should explain the observable configuration without claiming exploitation.

---

## 30. Redirect Scanner

### 30.1 Purpose

The Redirect Scanner analyzes HTTP-to-HTTPS behavior.

It records:

- Source URL
- HTTP status
- Location header
- Destination URL
- Redirect count
- Final destination

---

## 31. HTTP-to-HTTPS Redirect

Recommended behavior:

```
http://example.com
        |
       301
        |
        v
https://example.com
```

Accepted permanent redirect codes may include `301` and `308`.

A successful redirect should be: **PASS**

---

## 32. Missing HTTPS Redirect

If HTTP remains accessible without redirecting to HTTPS:

**Severity: HIGH**

Finding:

```
HTTP does not redirect to HTTPS.
```

The exact severity may be reduced if the application intentionally serves non-sensitive public HTTP content, but the default assessment should flag the absence.

---

## 33. Redirect Chain

The scanner should record each redirect step.

Example:

```
Step 1
HTTP
 |
301
 |
HTTPS

Step 2
HTTPS
 |
200
 |
Final Page
```

---

## 34. Redirect Loop

If a redirect loop is detected: **Severity: HIGH**

Example:

```
A -> B
B -> A
```

The scanner must stop following redirects after detecting the loop.

---

## 35. Excessive Redirects

If the redirect count exceeds the configured maximum: **Severity: MEDIUM**

The scan should stop safely.

---

## 36. Mixed Content Scanner

### 36.1 Purpose

The Mixed Content Scanner analyzes HTTPS HTML for resources loaded over HTTP.

Examples:

```html
<script src="http://...">
<img src="http://...">
<link href="http://...">
<iframe src="http://...">
```

---

## 37. Active Mixed Content

Potentially security-sensitive resource types include:

- JavaScript
- Iframe
- Stylesheet
- Object

These should receive higher priority.

Suggested severity: **HIGH** (depending on the resource and browser behavior)

---

## 38. Passive Mixed Content

Examples:

- Images
- Audio
- Video

These may be classified as **MEDIUM** or lower depending on context.

The scanner must clearly distinguish between active and passive mixed content.

---

## 39. Mixed Content Evidence

Example:

```json
{
  "page": "https://example.com",
  "resource": "http://cdn.example.com/script.js",
  "resource_type": "script",
  "mixed_content": true
}
```

---

## 40. Resource Scanner

The Resource Scanner identifies externally loaded resources.

Resource types:

- script
- stylesheet
- image
- iframe
- font
- media
- other

---

## 41. Same-Origin Analysis

A resource should be classified as same-origin when it belongs to the same origin as the scanned page.

Example:

```
https://example.com
https://example.com/app.js

Result:
same-origin
```

---

## 42. Third-Party Analysis

Example:

```
https://example.com
        |
        +-- https://cdn.example.net
        +-- https://analytics.example.org
        +-- https://external-service.com
```

These resources should be classified as `third-party` where appropriate.

Third-party presence is informational unless another security weakness is observed.

---

## 43. Third-Party Resource Categories

The system may categorize resources as:

- CDN
- Analytics
- Advertising
- External Service
- Font Provider
- Media Provider
- Unknown

Categorization should be conservative.

If the system cannot confidently categorize a resource, `Unknown` must be used instead of guessing.

---

## 44. Finding Generation

All scanner findings should use standardized structure.

```json
{
  "finding_code": "TLS_DEPRECATED_PROTOCOL",
  "category": "transport_security",
  "title": "Deprecated TLS protocol supported",
  "severity": "HIGH",
  "confidence": 1.0,
  "evidence": {},
  "impact": "...",
  "recommendation": "..."
}
```

---

## 45. Finding Codes

Initial finding codes:

```
TLS_CERT_EXPIRED
TLS_CERT_HOSTNAME_MISMATCH
TLS_CERT_SELF_SIGNED
TLS_CERT_CHAIN_INVALID
TLS_CERT_EXPIRING_SOON

TLS_1_0_ENABLED
TLS_1_1_ENABLED

HEADER_HSTS_MISSING
HEADER_HSTS_WEAK
HEADER_CSP_MISSING
HEADER_CSP_WEAK
HEADER_NOSNIFF_MISSING
HEADER_XFRAME_MISSING
HEADER_REFERRER_POLICY_MISSING
HEADER_PERMISSIONS_POLICY_MISSING

COOKIE_SECURE_MISSING
COOKIE_HTTPONLY_MISSING
COOKIE_SAMESITE_MISSING
COOKIE_SAMESITE_NONE_WITHOUT_SECURE

HTTP_NO_HTTPS_REDIRECT
REDIRECT_LOOP
REDIRECT_EXCESSIVE

MIXED_CONTENT_ACTIVE
MIXED_CONTENT_PASSIVE

THIRD_PARTY_RESOURCE
```

---

## 46. Severity Matrix

Initial severity matrix:

| Finding | Severity |
|---|---|
| Expired certificate | CRITICAL |
| Hostname mismatch | CRITICAL |
| Invalid certificate chain | HIGH |
| Self-signed public certificate | HIGH |
| Certificate expiring 1-6 days | HIGH |
| TLS 1.0 enabled | HIGH |
| TLS 1.1 enabled | HIGH |
| Missing HSTS | HIGH |
| HTTP not redirected to HTTPS | HIGH |
| Active mixed content | HIGH |
| Weak CSP | MEDIUM |
| Missing CSP | MEDIUM |
| Session cookie without Secure | MEDIUM |
| Session cookie without HttpOnly | MEDIUM |
| SameSite=None without Secure | HIGH |
| Passive mixed content | MEDIUM |
| Excessive redirects | MEDIUM |
| Missing X-Content-Type-Options | LOW |
| Missing X-Frame-Options | LOW |
| Missing Referrer-Policy | LOW |
| Missing Permissions-Policy | LOW |
| Third-party resource | INFO |

These classifications are baseline rules and may be refined after controlled testing.

---

## 47. Confidence Model

Confidence should represent the reliability of the evidence.

Suggested values:

| Confidence | Meaning |
|---|---|
| 1.00 | Directly observed and deterministic |
| 0.90 - 0.99 | Strong evidence |
| 0.70 - 0.89 | Good evidence with some uncertainty |
| 0.50 - 0.69 | Limited evidence |
| < 0.50 | Should generally not generate a strong security finding |

---

## 48. Evidence Requirements

Every non-informational security finding should contain evidence.

Example:

```json
{
  "header": "Strict-Transport-Security",
  "observed": false
}
```

or:

```json
{
  "protocol": "TLSv1.0",
  "supported": true
}
```

or:

```json
{
  "certificate": {
    "not_after": "2026-09-15T00:00:00",
    "days_remaining": 3
  }
}
```

---

## 49. Evidence Integrity

The scanner must preserve the difference between **Observed** and **Inferred**.

Observed evidence should be preferred.

Example:

- Observed: `HSTS header absent.`
- Correct conclusion: `HSTS was not observed in the tested response.`
- Incorrect conclusion: `The website is definitely vulnerable to interception.`

The scanner must avoid unsupported claims.

---

## 50. Scanner Failure Handling

If an individual scanner fails:

```
Scanner
   |
   v
Error
   |
   v
Record Failure
   |
   v
Continue Other Scanners
```

Example:

```json
{
  "scanner": "content",
  "status": "failed",
  "error_code": "RESPONSE_TOO_LARGE"
}
```

A scanner failure must not be interpreted as **PASS** or **No vulnerabilities**.

---

## 51. Network Timeout

If the target does not respond within configured limits: `TARGET_TIMEOUT`

The scanner should stop safely.

The report should state:

```
The target could not be fully assessed because
the request timed out.
```

---

## 52. Unsupported Target

If a target cannot be analyzed: `UNSUPPORTED_TARGET`

The system should explain why the assessment could not be completed.

---

## 53. Maximum Response Size

The scanner must enforce a maximum response size.

If exceeded: `RESPONSE_TOO_LARGE`

The scanner must stop reading the response. This prevents excessive memory consumption.

---

## 54. Maximum Redirects

The scanner should enforce a configurable redirect limit.

Example: `MAX_REDIRECTS = 10`

If exceeded: `REDIRECT_LIMIT_REACHED`

The scan should stop following redirects.

---

## 55. Maximum Resources

The Content Scanner must not analyze an unlimited number of resources.

Example: `MAX_RESOURCES = 100`

The exact value may be adjusted during implementation.

---

## 56. Scanner Execution Order

Recommended execution order:

```
1. Target Validation
       |
2. TLS Analysis
       |
3. HTTP Analysis
       |
4. Redirect Analysis
       |
5. Header Analysis
       |
6. Cookie Analysis
       |
7. Content Analysis
       |
8. Resource Analysis
       |
9. Finding Generation
       |
10. Risk Scoring
       |
11. AI Explanation
       |
12. Report Generation
```

---

## 57. Scanner Independence

Each scanner must remain independently testable.

Example:

```
tests/
|
+-- scanners/
    +-- test_tls_scanner.py
    +-- test_header_scanner.py
    +-- test_cookie_scanner.py
    +-- test_redirect_scanner.py
    +-- test_content_scanner.py
    +-- test_resource_scanner.py
```

---

## 58. Unit Testing Requirements

Each scanner should have tests for:

**TLS**
- Valid certificate
- Expired certificate
- Hostname mismatch
- Self-signed certificate
- TLS 1.0 support
- TLS 1.1 support
- Modern TLS configuration

**Headers**
- Missing HSTS
- Valid HSTS
- Missing CSP
- Weak CSP
- Missing X-Content-Type-Options
- Missing X-Frame-Options
- Missing Referrer-Policy
- Missing Permissions-Policy

**Cookies**
- Secure cookie
- Missing Secure
- Missing HttpOnly
- Missing SameSite
- SameSite=None without Secure

**Redirects**
- HTTP to HTTPS
- No redirect
- Redirect loop
- Excessive redirects

**Content**
- No mixed content
- Active mixed content
- Passive mixed content

**Resources**
- Same-origin resource
- Third-party resource
- CDN resource
- Unknown resource

---

## 59. Deterministic Detection

Security detection must be deterministic.

Example:

```
Input:
Strict-Transport-Security header absent

Rule:
HEADER_HSTS_MISSING

Output:
Severity = HIGH
Confidence = 1.0
```

The AI must not change this result.

---

## 60. Risk Engine Input

The Risk Engine receives structured findings.

Example:

```
Finding 1
Severity: HIGH
Category: TLS

Finding 2
Severity: MEDIUM
Category: Cookies

Finding 3
Severity: LOW
Category: Headers
```

The Risk Engine then calculates:

- Overall Score
- Risk Level
- Priority

---

## 61. Scanner Output Pipeline

```
Raw Target Response
        |
        v
Scanner
        |
        v
Observed Evidence
        |
        v
Detection Rule
        |
        v
Finding
        |
        v
Severity
        |
        v
Confidence
        |
        v
Risk Engine
```

---

## 62. What the Scanner Must Never Do

The scanner must never:

- Exploit
- Brute Force
- Attack
- Modify
- Delete
- Upload
- Bypass
- Authenticate
- Crack
- Flood

The project is a defensive configuration auditor.

---

## 63. False Positive Prevention

The scanner should prefer conservative findings.

For example:

- **Incorrect:** Third-party script detected = Vulnerability
- **Correct:** Third-party script detected = Informational observation

Another example:

- **Incorrect:** CSP missing = XSS vulnerability confirmed
- **Correct:** CSP missing = Security hardening weakness

---

## 64. False Negative Awareness

The scanner must clearly communicate that passing a check does not prove complete security.

Example:

- **PASS:** `No issue was detected by this specific security configuration check.`
- **Not:** `Website is completely secure.`

---

## 65. Scanner Result Example

A complete scan may produce:

```json
{
  "scan": {
    "target": "https://example.com",
    "status": "completed"
  },
  "findings": [
    {
      "code": "HEADER_HSTS_MISSING",
      "severity": "HIGH",
      "confidence": 1.0
    },
    {
      "code": "TLS_1_0_ENABLED",
      "severity": "HIGH",
      "confidence": 1.0
    },
    {
      "code": "COOKIE_HTTPONLY_MISSING",
      "severity": "MEDIUM",
      "confidence": 0.92
    }
  ]
}
```

---

## 66. Scanner Quality Principles

Every scanner implementation must follow:

**Principle 1 — Evidence First**
Never create a finding without supporting evidence.

**Principle 2 — Conservative Classification**
Do not exaggerate severity.

**Principle 3 — Deterministic Rules**
The same evidence must produce the same finding.

**Principle 4 — Safe Requests**
Never perform destructive operations.

**Principle 5 — Bounded Resources**
Every network and parsing operation must have limits.

**Principle 6 — Explainable Findings**
Every finding must explain why it was generated.

**Principle 7 — Independent Modules**
Scanners should remain independently testable.

---

## 67. MVP Scanner Priority

The implementation priority is:

**Priority 1**
- TLS Scanner
- Security Header Scanner

**Priority 2**
- Cookie Scanner
- Redirect Scanner

**Priority 3**
- Content Scanner
- Resource Scanner

**Priority 4**
- Advanced configuration checks

The team should complete and test Priority 1 before expanding the scanner surface.

---

## 68. Final Scanner Architecture

```
                  TARGET URL
                      |
                      v
               URL VALIDATOR
                      |
                      v
                SCAN ENGINE
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
      TLS           HTTP          CONTENT
    Scanner        Scanner         Scanner
       |              |              |
       |         +----+----+         |
       |         |         |         |
       |       Headers   Cookies   Resources
       |         |         |         |
       +---------+---------+---------+
                      |
                      v
               FINDING ENGINE
                      |
                      v
                 RISK ENGINE
                      |
               +------+------+
               |             |
               v             v
             MySQL          AI
               |             |
               +------+------+
                      |
                      v
                FINAL REPORT
```

---

## 69. Final Design Rule

The most important rule of the scanner architecture is:

> The scanner discovers. Evidence proves. Rules classify. The risk engine prioritizes. AI explains.

AI must never be treated as the primary security detection mechanism.

The security scanner remains the authoritative source for technical findings.