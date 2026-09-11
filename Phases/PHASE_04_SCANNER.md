# PHASE 04 — CORE SECURITY SCANNER

## 1. Phase Overview

**Phase:** 04  
**Name:** Core Security Scanner  
**Status:** Planned  
**Depends On:** Phase 03 — Secure Target Validation  
**Next Phase:** Phase 05 — Finding & Risk Engine

---

## 2. Objective

Phase 04 ka objective deterministic security scanning engine implement
karna hai.

Scanner authorized target ke security configuration ko inspect karega
aur raw security observations generate karega.

Primary scanning areas:

- TLS configuration
- TLS protocol versions
- TLS certificate
- Certificate validity
- Certificate hostname
- Certificate expiration
- HTTP security headers
- HSTS
- Content Security Policy
- X-Content-Type-Options
- X-Frame-Options / frame protection
- Referrer-Policy
- Permissions-Policy
- Cookie security attributes
- HTTPS enforcement
- Redirect behavior
- HTTP response metadata

---

## 3. Core Principle

The scanner must be:

> **Deterministic, explainable, repeatable and security-first.**

Same target configuration ke liye scanner ko same raw observations
produce karne chahiye.

AI scanner ke raw security results decide nahi karega.

```text
Target
  |
  v
Phase 03
Safe Network
  |
  v
Security Scanner
  |
  +--> TLS Checks
  |
  +--> Certificate Checks
  |
  +--> HTTP Checks
  |
  +--> Cookie Checks
  |
  +--> Redirect Checks
  |
  v
Raw Security Observations
```

---

## 4. Documents To Follow

Implementation se pehle ye documents read karna mandatory hai:

```
Docs/
├── SRS.md
├── ARCHITECTURE.md
├── DATABASE.md
├── SCANNER_SPECIFICATION.md
├── SECURITY.md
├── API.md
├── AI_MODEL.md
├── UI_UX.md
├── TESTING.md
├── DEPLOYMENT.md
├── DEMO.md
└── ROADMAP.md
```

Also read:

```
Phases/PHASE_01_FOUNDATION.md
Phases/PHASE_02_DATABASE.md
Phases/PHASE_03_TARGET_SECURITY.md
Phases/PHASE_04_SCANNER.md
```

---

## 5. Scope

### Included

Phase 04 mein:

- Scanner orchestration foundation
- TLS inspection
- TLS protocol detection
- Certificate inspection
- Certificate validation
- HTTP response inspection
- Security header inspection
- HSTS inspection
- CSP inspection
- Cookie security inspection
- HTTPS redirect inspection
- Raw observation generation
- Scanner timeout handling
- Scanner error handling
- Scanner result normalization
- Scanner unit tests
- Scanner integration tests

### Not Included

Phase 04 mein implement nahi karna:

- Risk score calculation
- Finding severity calculation
- AI explanation
- AI-generated recommendations
- User dashboard
- Report generation
- Email notifications
- Background job system
- Production deployment automation

Ye later phases mein implement honge.

---

## 6. Scanner Architecture

Scanner modular hona chahiye.

```
Core Scanner
    |
    +-- TLS Scanner
    |
    +-- Certificate Scanner
    |
    +-- HTTP Scanner
    |
    +-- Header Scanner
    |
    +-- Cookie Scanner
    |
    +-- Redirect Scanner
    |
    v
Raw Scan Result
```

Har scanner module ka single responsibility hona chahiye.

---

## 7. Mandatory Network Rule

Phase 04 scanner directly arbitrary network requests nahi karega.

Incorrect:

```
Scanner
   |
   v
httpx.get(user_url)
```

Correct:

```
User URL
   |
   v
Phase 03 Validator
   |
   v
Safe Network Client
   |
   v
Scanner
```

Phase 03 ki security boundary ko bypass karna strictly prohibited hai.

---

## 8. Scanner Orchestrator

Suggested component:

```
app/scanners/scanner.py
```

Responsibilities:

- scanner modules execute karna
- execution order maintain karna
- timeout boundaries enforce karna
- partial failures handle karna
- results collect karna
- normalized raw result return karna

Concept:

```
Scanner
   |
   +--> TLS
   |
   +--> Certificate
   |
   +--> HTTP
   |
   +--> Headers
   |
   +--> Cookies
   |
   +--> Redirects
   |
   v
ScanResult
```

---

## 9. Scanner Modules

Suggested structure:

```
app/
└── scanners/
    ├── __init__.py
    ├── scanner.py
    ├── tls_scanner.py
    ├── certificate_scanner.py
    ├── http_scanner.py
    ├── header_scanner.py
    ├── cookie_scanner.py
    └── redirect_scanner.py
```

Exact paths architecture ke according adjust kiye ja sakte hain.

---

## 10. TLS Scanner

TLS scanner HTTPS targets ke TLS configuration ko inspect karega.

Primary checks:

- TLS availability
- TLS protocol version
- TLS handshake success
- Certificate availability
- Certificate chain information
- Negotiated security parameters
- Deprecated protocol detection

---

## 11. TLS Protocol Checks

Scanner supported/negotiated TLS protocol ko identify karega.

Security policy ke according deprecated/insecure protocols identify
kiye jayenge.

Concept:

```
HTTPS Target
    |
    v
TLS Handshake
    |
    v
Protocol
    |
    +--> Modern
    |
    +--> Deprecated
    |
    +--> Unsupported
```

Exact accepted/deprecated versions must follow:

```
Docs/SCANNER_SPECIFICATION.md
```

Do not invent additional severity rules inside the scanner.

---

## 12. TLS Handshake

TLS handshake ko controlled timeout ke andar perform karna hoga.

Failures:

- connection refused
- handshake failure
- certificate failure
- protocol mismatch
- timeout

application crash nahi karne chahiye.

Example:

```
TLS Handshake
     |
     +---- Success
     |
     +---- Timeout
     |
     +---- Failure
```

Failure ko structured raw observation ke form mein return karna chahiye.

---

## 13. Certificate Scanner

Certificate scanner certificate metadata collect karega.

Possible observations:

- Subject
- Issuer
- Valid from
- Valid until
- SAN entries
- Signature algorithm
- Public key information
- Certificate chain information
- Expiration state

Sensitive private key material kabhi collect nahi karna.

---

## 14. Certificate Validity

Scanner check karega:

```
Current Time
     |
     v
Certificate Validity
     |
     +--> Not Yet Valid
     |
     +--> Currently Valid
     |
     +--> Expired
```

Clock handling timezone-aware hona chahiye.

---

## 15. Certificate Expiration

Certificate expiration ko deterministic observation ke form mein store
kiya jayega.

Conceptual values:

```
expires_at
days_until_expiry
is_expired
```

Exact finding/severity later Phase 05 mein determine hogi.

---

## 16. Certificate Hostname

Scanner ko verify karna chahiye ki certificate target hostname ke liye
valid hai.

Example:

```
Target:
example.com

Certificate SAN:
example.com
www.example.com
```

Matching certificate:

```
VALID
```

Mismatch:

```
HOSTNAME_MISMATCH
```

Hostname validation trusted TLS/library functionality ke through honi
chahiye.

Manual wildcard matching avoid karein unless explicitly required.

---

## 17. Certificate Chain

Scanner certificate chain ke available metadata ko inspect karega.

Potential observations:

- chain available
- issuer
- chain validation result
- trust failure
- incomplete chain

Scanner ko private certificate/key material retrieve nahi karna.

---

## 18. HTTP Scanner

HTTP scanner safe network client ke through response inspect karega.

Collectable data:

- HTTP status code
- final URL
- response headers
- content type
- server metadata where appropriate
- redirect information
- cookies
- security headers

Response body ko unnecessarily download nahi karna.

---

## 19. Response Body Limit

Scanner ka primary purpose security configuration inspect karna hai.

Large response body ki need nahi honi chahiye.

Therefore:

```
HTTP Response
     |
     v
Response Size Limit
     |
     +--> Within Limit
     |
     +--> Too Large
```

Configured limits Phase 03 ke safe network policy ke according apply honge.

---

## 20. Security Header Scanner

Security headers ko individually inspect kiya jayega.

Primary headers:

```
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
```

Exact header list:

`Docs/SCANNER_SPECIFICATION.md` is authoritative.

---

## 21. HSTS Detection

Header:

```
Strict-Transport-Security
```

inspect kiya jayega.

Raw observations may include:

- present
- value
- max_age
- include_subdomains
- preload

Parser malformed directives ko safely handle kare.

---

## 22. HSTS Parsing

Example:

```
Strict-Transport-Security:
max-age=31536000; includeSubDomains; preload
```

Scanner structured information extract kare:

```
max_age = 31536000
include_subdomains = true
preload = true
```

Malformed values application crash nahi karne chahiye.

---

## 23. CSP Detection

Header:

```
Content-Security-Policy
```

inspect kiya jayega.

Scanner raw policy ko safely parse/normalize kar sakta hai.

Potential observations:

- header_present
- policy
- directive_names

Scanner CSP policy ko directly risk score nahi karega.

Risk interpretation Phase 05 mein hogi.

---

## 24. X-Content-Type-Options

Scanner check karega:

```
X-Content-Type-Options
```

Expected security configuration according to scanner specification
document ki jayegi.

Case-insensitive HTTP header handling mandatory hai.

---

## 25. Frame Protection

Scanner frame protection configuration inspect karega.

Relevant headers:

```
X-Frame-Options
Content-Security-Policy
```

Duplicate/overlapping protection ko raw observation level par represent
kiya jayega.

Severity later determine hogi.

---

## 26. Referrer Policy

Inspect:

```
Referrer-Policy
```

Scanner configured value capture karega.

Unknown or malformed values ko safely identify kare.

---

## 27. Permissions Policy

Inspect:

```
Permissions-Policy
```

Header presence and parseable policy information capture ki ja sakti hai.

Exact policy quality evaluation:

`Docs/SCANNER_SPECIFICATION.md`

ke according honi chahiye.

---

## 28. Cookie Scanner

HTTP response ke Set-Cookie headers inspect kiye jayenge.

Important attributes:

```
Secure
HttpOnly
SameSite
Path
Domain
Max-Age
Expires
```

---

## 29. Cookie Security Observations

Example:

```
Set-Cookie
    |
    +--> Secure
    +--> HttpOnly
    +--> SameSite
    +--> Domain
    +--> Path
```

Scanner raw attributes capture karega.

Risk/severity Phase 05 mein calculate hogi.

---

## 30. Cookie Parsing

Cookie parsing robust honi chahiye.

Handle:

- multiple cookies
- repeated headers
- quoted values
- optional attributes
- malformed cookies
- case variations

Malformed cookie ko application crash nahi karna chahiye.

---

## 31. HTTPS Enforcement

HTTP target behavior inspect kiya jayega.

Concept:

```
http://example.com
       |
       v
HTTP Request
       |
       v
Response
       |
       +--> HTTPS Redirect
       |
       +--> No Redirect
```

Redirect behavior raw result ke form mein capture hoga.

---

## 32. Redirect Scanner

Redirect chain inspect ki jayegi.

Capture:

```
initial_url
redirect_count
redirect_chain
final_url
status_codes
```

Every redirect destination must still pass Phase 03 validation.

---

## 33. Redirect Security

Unsafe redirect:

```
Public
  |
  v
Private
  |
  X
Blocked
```

Safe redirect:

```
HTTP
 |
 v
HTTPS
 |
 v
Public Target
```

Allowed.

Phase 03 remains authoritative for destination safety.

---

## 34. HTTP Header Normalization

HTTP header names case-insensitive hote hain.

Scanner ko:

```
Content-Security-Policy
content-security-policy
CONTENT-SECURITY-POLICY
```

ko same logical header treat karna chahiye.

Duplicate headers ko blindly overwrite nahi karna.

---

## 35. Raw Observation Model

Phase 04 ka output findings nahi hai.

Output:

```
Raw Security Observations
```

Concept:

```
Observation
├── check_id
├── category
├── status
├── observed_value
├── expected_value
├── evidence
└── metadata
```

Exact schema project architecture ke according implement hoga.

---

## 36. Observation vs Finding

Important distinction:

```
Phase 04
Raw Observation
      |
      v
Phase 05
Finding
      |
      v
Severity
      |
      v
Risk Score
```

Phase 04 mein severity calculate nahi karni.

---

## 37. Check IDs

Every security check ka stable identifier hona chahiye.

Example:

```
TLS_PROTOCOL
TLS_CERTIFICATE
TLS_CERT_EXPIRY
TLS_CERT_HOSTNAME
HTTP_HSTS
HTTP_CSP
HTTP_X_CONTENT_TYPE_OPTIONS
HTTP_FRAME_PROTECTION
HTTP_REFERRER_POLICY
HTTP_PERMISSIONS_POLICY
HTTP_COOKIE_SECURITY
HTTP_HTTPS_REDIRECT
```

Exact IDs `SCANNER_SPECIFICATION.md` se derive honge.

IDs ko casually rename nahi karna because later database/reporting depend
kar sakti hai.

---

## 38. Scanner Result Structure

Conceptual:

```
ScanResult
├── target
├── started_at
├── completed_at
├── scanner_version
├── tls
├── certificate
├── http
├── headers
├── cookies
├── redirects
└── observations
```

Exact database mapping Phase 02/06 architecture ke according hogi.

---

## 39. Partial Failure Handling

Ek scanner module fail hone par entire scan unnecessarily crash nahi hona
chahiye.

Example:

```
TLS Scanner
    |
    X failure

HTTP Scanner
    |
    v
Continue
```

Result:

```
TLS = unavailable
HTTP = completed
```

Structured failure information preserve honi chahiye.

---

## 40. Scanner Error Model

Errors categories:

```
NETWORK_ERROR
TLS_ERROR
CERTIFICATE_ERROR
HTTP_ERROR
TIMEOUT
PARSER_ERROR
UNSUPPORTED_TARGET
SCAN_MODULE_ERROR
```

Errors predictable and machine-readable hone chahiye.

---

## 41. Timeout Strategy

Har scanner module bounded execution mein run hona chahiye.

Example:

```
Global Scan Timeout
       |
       +--> TLS
       |
       +--> Certificate
       |
       +--> HTTP
       |
       +--> Headers
       |
       +--> Cookies
       |
       +--> Redirects
```

Infinite blocking prohibited hai.

---

## 42. Resource Safety

Scanner:

- unlimited response bodies read nahi karega
- unlimited redirects follow nahi karega
- unlimited retries nahi karega
- unlimited concurrent connections nahi banayega
- unbounded certificate chains process nahi karega
- giant headers/parser input ko blindly process nahi karega

---

## 43. Concurrency

Initial implementation mein simplicity and safety priority hai.

Scanner modules ko unnecessarily parallelize nahi karna.

Agar concurrency use hoti hai:

- bounded
- configurable
- timeout-controlled
- resource-aware

honi chahiye.

---

## 44. Determinism

Scanner decisions deterministic hone chahiye.

Avoid:

- random severity
- random check order
- AI-generated detection
- uncontrolled external intelligence

Same input/configuration se equivalent raw observations expected hain.

---

## 45. No AI In Detection

Strict rule:

```
AI
 X
 |
 +--> Detect TLS weakness
 +--> Decide severity
 +--> Decide score
```

Correct:

```
Scanner
  |
  v
Raw Observation
  |
  v
Finding Engine
  |
  v
Risk Engine
  |
  v
AI Explanation
```

AI only later explanation layer mein use hoga.

---

## 46. Test Strategy

Phase 04 ke liye automated tests mandatory hain.

Testing categories:

- Unit Tests
- Integration Tests
- TLS Tests
- HTTP Tests
- Header Tests
- Cookie Tests
- Redirect Tests
- Failure Tests
- Regression Tests

---

## 47. TLS Tests

Test:

- TLS handshake success
- TLS handshake failure
- supported protocol
- deprecated protocol
- certificate present
- certificate expired
- certificate not-yet-valid
- hostname mismatch
- certificate parsing failure
- TLS timeout

Controlled test certificates and local fixtures use karein.

---

## 48. HTTP Tests

Test:

- status code
- response headers
- missing headers
- present headers
- duplicate headers
- malformed headers
- HTTP error
- timeout
- response size limit

---

## 49. HSTS Tests

Test:

- Missing HSTS
- Valid HSTS
- Different max-age
- includeSubDomains
- preload
- Malformed max-age
- Malformed directive

Expected raw observations verify karein.

---

## 50. CSP Tests

Test:

- Missing CSP
- Basic CSP
- Multiple directives
- Malformed CSP
- Duplicate CSP headers

Parser crash nahi hona chahiye.

---

## 51. Cookie Tests

Test:

- Secure cookie
- HttpOnly cookie
- SameSite cookie
- Missing Secure
- Missing HttpOnly
- Missing SameSite
- Multiple cookies
- Malformed cookie

Raw attributes correctly extract hone chahiye.

---

## 52. Redirect Tests

Test:

- No redirect
- HTTP -> HTTPS
- Multiple redirects
- Redirect loop
- Unsafe redirect
- Private redirect
- Metadata redirect
- Unsupported scheme redirect

Phase 03 security validation mandatory verify karein.

---

## 53. Integration Test

Controlled local test server create karein:

```
Test Server
     |
     +--> TLS configuration
     |
     +--> HTTP headers
     |
     +--> Cookies
     |
     +--> Redirects
```

Expected observations compare karein.

---

## 54. Regression Tests

Phase 04 complete hone ke baad:

```
Phase 01 tests
Phase 02 tests
Phase 03 tests
Phase 04 tests
```

sab pass hone chahiye.

Existing functionality break nahi honi chahiye.

---

## 55. Security Requirements

Scanner must:

- use Phase 03 safe network layer
- enforce timeouts
- respect response limits
- validate redirects
- avoid sensitive logging
- avoid credential collection
- never store private keys
- never execute remote content
- never upload target content unnecessarily
- never bypass target validation

---

## 56. Logging Requirements

Useful events:

- scan module started
- scan module completed
- scan module failed
- TLS handshake completed
- HTTP response received
- parser failure
- scanner timeout

Do not log:

- passwords
- authorization tokens
- session cookies
- private keys
- API keys
- sensitive query parameters

---

## 57. Data Minimization

Scanner ko sirf security audit ke liye required information collect karni
chahiye.

Avoid storing:

- complete response bodies
- unnecessary HTML
- authentication credentials
- private certificate keys
- sensitive cookie values

Cookie values should be redacted or omitted from persisted evidence.

---

## 58. Performance

Scanner reasonable time mein complete hona chahiye.

Avoid:

- duplicate network requests
- unnecessary TLS handshakes
- unnecessary redirects
- repeated parsing
- unbounded retries

Security correctness > premature optimization.

---

## 59. Suggested Project Structure

```
app/
├── scanners/
│   ├── __init__.py
│   ├── scanner.py
│   ├── tls_scanner.py
│   ├── certificate_scanner.py
│   ├── http_scanner.py
│   ├── header_scanner.py
│   ├── cookie_scanner.py
│   └── redirect_scanner.py
│
├── schemas/
│   └── scan_result.py
│
└── services/
    └── safe_http_client.py

tests/
└── scanners/
    ├── test_scanner.py
    ├── test_tls_scanner.py
    ├── test_certificate_scanner.py
    ├── test_http_scanner.py
    ├── test_header_scanner.py
    ├── test_cookie_scanner.py
    └── test_redirect_scanner.py
```

---

## 60. Acceptance Criteria

Phase 04 accepted tab hoga jab:

- [ ] Scanner orchestrator implemented
- [ ] TLS scanner implemented
- [ ] Certificate scanner implemented
- [ ] HTTP scanner implemented
- [ ] Header scanner implemented
- [ ] Cookie scanner implemented
- [ ] Redirect scanner implemented
- [ ] Stable check IDs implemented
- [ ] Raw observation model implemented
- [ ] No severity logic in scanner
- [ ] No risk scoring in scanner
- [ ] No AI detection logic
- [ ] Phase 03 safe client used
- [ ] Redirects validated
- [ ] Timeouts enforced
- [ ] Response limits enforced
- [ ] Sensitive data minimized
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Existing tests remain green

---

## 61. Definition of Done

Phase 04 complete tab mana jayega jab:

```
Safe Target
    |
    v
Scanner
    |
    +--> TLS
    +--> Certificate
    +--> HTTP
    +--> Headers
    +--> Cookies
    +--> Redirects
    |
    v
Raw Observations
```

reliably generate ho rahe hon.

Scanner deterministic hona chahiye aur Phase 05 ke Finding & Risk Engine
ko clean structured input provide karna chahiye.

---

## 62. Expected Deliverables

Phase 04 ke end tak:

- Core Scanner
- TLS Scanner
- Certificate Scanner
- HTTP Scanner
- Header Scanner
- Cookie Scanner
- Redirect Scanner
- Observation Models
- Scanner Error Handling
- Scanner Tests
- Integration Fixtures
- Security Tests
- Documentation Updates

---

## 63. AI Coding Agent Prompt

```
You are implementing PHASE 04 of the
AI-Powered Web Security Configuration Auditor.

Read ALL project documentation before modifying code:

Docs/SRS.md
Docs/ARCHITECTURE.md
Docs/DATABASE.md
Docs/SCANNER_SPECIFICATION.md
Docs/SECURITY.md
Docs/API.md
Docs/AI_MODEL.md
Docs/UI_UX.md
Docs/TESTING.md
Docs/DEPLOYMENT.md
Docs/DEMO.md
Docs/ROADMAP.md

Also read:

Phases/PHASE_01_FOUNDATION.md
Phases/PHASE_02_DATABASE.md
Phases/PHASE_03_TARGET_SECURITY.md
Phases/PHASE_04_SCANNER.md

TASK:

Implement ONLY PHASE 04 — CORE SECURITY SCANNER.

PRIMARY GOAL:

Build a deterministic, modular security scanner that operates only
through the secure networking boundary implemented in Phase 03.

MANDATORY ARCHITECTURE:

User Target
 -> Phase 03 Target Validation
 -> Safe Network Client
 -> Phase 04 Scanner
 -> Raw Security Observations

NEVER allow scanner modules to directly use a raw user-controlled URL
for arbitrary network access.

IMPLEMENT:

1. Scanner orchestrator.
2. TLS scanner.
3. Certificate scanner.
4. HTTP scanner.
5. Security header scanner.
6. Cookie scanner.
7. Redirect scanner.
8. Stable check IDs.
9. Structured raw observation model.
10. Structured scanner errors.
11. Module-level timeouts.
12. Resource limits.
13. Partial failure handling.
14. Comprehensive automated tests.

TLS CHECKS:

- TLS availability
- negotiated protocol
- deprecated protocol detection
- handshake status
- certificate information
- certificate validity
- certificate expiration
- certificate hostname validation
- certificate chain information where available

HTTP CHECKS:

- status code
- response headers
- HTTPS redirect behavior
- redirect chain
- relevant security headers

HEADER CHECKS:

- Strict-Transport-Security
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options / frame protection
- Referrer-Policy
- Permissions-Policy

COOKIE CHECKS:

- Secure
- HttpOnly
- SameSite
- Path
- Domain
- expiration-related attributes where appropriate

IMPORTANT:

Use Docs/SCANNER_SPECIFICATION.md as the authoritative source for
exact checks and expected behavior.

Do NOT invent new security scoring rules.

PHASE 04 OUTPUT:

The scanner produces RAW SECURITY OBSERVATIONS.

It must NOT calculate:

- severity
- risk score
- business impact
- AI explanation
- remediation text

Those belong to later phases.

DO NOT IMPLEMENT:

- Finding engine
- Risk engine
- AI
- Dashboard
- Reports
- Notifications
- Background job infrastructure
- Production deployment automation

SECURITY:

- Always use Phase 03 safe network client.
- Validate every redirect.
- Enforce network timeouts.
- Enforce response size limits.
- Never store private keys.
- Never expose credentials.
- Redact sensitive cookie values.
- Do not log authentication tokens.
- Do not download unnecessary response bodies.
- Do not execute remote content.
- Do not bypass SSRF protection.

TESTING:

Create controlled local/mock fixtures.

Test:

- TLS success
- TLS failure
- TLS timeout
- protocol detection
- expired certificate
- not-yet-valid certificate
- hostname mismatch
- certificate parsing failure
- HTTP status codes
- missing headers
- present headers
- duplicate headers
- malformed headers
- HSTS
- CSP
- X-Content-Type-Options
- frame protection
- Referrer-Policy
- Permissions-Policy
- cookie attributes
- multiple cookies
- malformed cookies
- HTTP -> HTTPS redirect
- multiple redirects
- redirect loop
- unsafe redirect
- private redirect
- metadata redirect
- timeout
- oversized response

Do not perform unauthorized scans against real infrastructure.

Use mocks and controlled test servers.

QUALITY:

- Type hints
- Small functions
- Single responsibility
- Clear naming
- No duplicated scanner logic
- Structured errors
- Testable components
- Maintain existing architecture
- Do not rewrite Phase 01/02/03 unnecessarily
- Do not introduce new frameworks

After implementation:

1. Run formatter/linter if configured.
2. Run Phase 04 tests.
3. Run all existing tests.
4. Fix regressions.
5. Verify application startup.
6. Verify imports.
7. Verify type checking where configured.
8. Report all changed files.
9. Report exact test results.
10. Report unresolved issues.

Do not claim completion without actually running tests.

The implementation must be production-oriented,
secure, deterministic, modular, and maintainable.
```

---

## 64. Phase Completion Record

After implementation:

```
Phase: 04
Status: Completed / Pending

Implemented:
- Scanner Orchestrator
- TLS Scanner
- Certificate Scanner
- HTTP Scanner
- Header Scanner
- Cookie Scanner
- Redirect Scanner
- Raw Observation Model

Tests:
- Unit: ___
- Integration: ___
- Security: ___
- Total: ___

Result:
PASS / FAIL

Known Issues:
- None / ...

Approved For:
Phase 05 — Finding & Risk Engine
```

---

## 65. Transition To Phase 05

Phase 04 ke baad scanner raw security observations generate karega.

Next phase in observations ko meaningful security findings mein convert
karega.

```
Phase 04
Raw Observations
       |
       v
Phase 05
Finding Engine
       |
       v
Severity
       |
       v
Risk Engine
       |
       v
Deterministic Risk Score
```

Phase 05 ka primary objective scanner output ko:

- findings
- severity
- evidence
- remediation mapping
- deterministic risk score

mein convert karna hoga.

---

### FINAL PRINCIPLE

The scanner detects facts.
The finding engine interprets those facts.
The risk engine calculates risk.
AI explains the results.

These responsibilities must remain strictly separated.