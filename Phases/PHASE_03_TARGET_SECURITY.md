# PHASE 03 — SECURE TARGET VALIDATION

## 1. Phase Overview

**Phase:** 03  
**Name:** Secure Target Validation & SSRF Protection  
**Status:** Planned  
**Depends On:** Phase 01 — Foundation, Phase 02 — Database  
**Next Phase:** Phase 04 — Core Security Scanner

---

## 2. Objective

Phase 03 ka primary objective ek strong security boundary implement karna hai
jo scanner ko user-controlled target URLs ke unsafe use se protect kare.

Scanner kisi bhi user-provided URL ko directly network request ke liye use
NAHI karega.

Har target ko outbound connection se pehle:

1. Parse
2. Normalize
3. Validate
4. Resolve
5. IP classify
6. Security policy check
7. Safe connection configuration

ke through pass hona hoga.

### Core Principle

> User-controlled URL must never directly control where the server connects.

---

## 3. Documents To Follow

Implementation strictly in documents ke according honi chahiye:

```text
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

### Priority

Agar kisi implementation decision mein conflict ho:

```
SECURITY.md
    ↓
SRS.md
    ↓
ARCHITECTURE.md
    ↓
SCANNER_SPECIFICATION.md
    ↓
Other Docs
```

---

## 4. Scope

### Included

Phase 03 mein following components implement honge:

- URL parsing
- URL normalization
- Scheme validation
- Hostname validation
- Port validation
- Credential rejection
- DNS resolution
- IPv4 classification
- IPv6 classification
- Private IP blocking
- Loopback blocking
- Link-local blocking
- Multicast blocking
- Reserved IP blocking
- Cloud metadata address blocking
- IPv4-mapped IPv6 protection
- DNS rebinding protection
- Redirect destination validation
- Safe outbound HTTP client configuration
- Connection timeout policy
- Network safety abstraction
- Security-focused tests

### Not Included

Phase 03 mein ye features implement nahi karne:

- TLS vulnerability scanning
- Certificate analysis
- HTTP security header detection
- CSP analysis
- Cookie security analysis
- HSTS detection
- Risk scoring
- AI explanation
- Report generation
- Dashboard implementation
- Full scan orchestration

Ye functionality later phases mein implement hogi.

---

## 5. Security Boundary

Target validation scanner architecture ka mandatory security boundary hoga.

```
User URL
   |
   v
URL Parser
   |
   v
Normalizer
   |
   v
Validator
   |
   v
DNS Resolver
   |
   v
IP Classifier
   |
   v
Security Policy
   |
   +---- BLOCK ----> Reject
   |
   v
Safe Network Client
   |
   v
Phase 04 Scanner
```

### Important

Phase 04 ka scanner directly httpx, requests, sockets, ya kisi
network library ko user-provided URL nahi dega.

Network access ke liye Phase 03 ka safe abstraction use karna mandatory hoga.

---

## 6. Target URL Policy

### 6.1 Allowed Schemes

Initial implementation mein only:

- `http://`
- `https://`

allow honge.

Following schemes reject honge:

- `file://`
- `ftp://`
- `gopher://`
- `data://`
- `javascript://`
- `ssh://`
- `telnet://`

Aur unknown/custom schemes bhi reject honge.

---

## 7. Hostname Validation

Target hostname:

- empty nahi hona chahiye
- valid hostname format mein hona chahiye
- unsupported characters reject hone chahiye
- credentials contain nahi karna chahiye
- hostname normalization ke baad validate hona chahiye

Example:

```
https://example.com
```

Valid.

Credentials:

```
https://user:password@example.com
```

Reject.

Reason:

Scanner ko user credentials carry karne wale URLs accept nahi karne chahiye.

---

## 8. Port Policy

Default ports:

```
HTTP  -> 80
HTTPS -> 443
```

Project security policy ke according explicitly allowed ports hi accept
kiye jayenge.

Unexpected or unsafe ports reject hone chahiye.

Port validation centralized honi chahiye.

Example abstraction:

```
validate_port(scheme, port)
```

Phase 03 ke baad scanner ko port policy manually implement nahi karni chahiye.

---

## 9. DNS Resolution

Hostname ko network request se pehle resolve karna mandatory hai.

Example:

```
example.com
     |
     v
DNS Resolution
     |
     +--> IPv4
     |
     +--> IPv6
```

Har resolved address ko security policy ke against check karna hoga.

---

## 10. Private IP Protection

Scanner private/internal addresses ko target nahi karega.

IPv4 private ranges:

```
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

IPv6 private/local ranges bhi block honge according to standard IP
classification.

---

## 11. Loopback Protection

Loopback addresses reject hone chahiye.

Examples:

```
127.0.0.0/8
::1
```

Reason:

```
User Target
    |
    v
Scanner Server
    |
    X
localhost
```

Scanner ko apne hi host ke internal services ko target karne ka mechanism
nahi banna chahiye.

---

## 12. Link-Local Protection

Link-local addresses reject hone chahiye.

IPv4 example:

```
169.254.0.0/16
```

IPv6 link-local ranges bhi reject honge.

---

## 13. Cloud Metadata Protection

Cloud metadata endpoints must always be blocked.

At minimum, scanner policy must reject:

```
169.254.169.254
```

This protection must not depend only on hostname filtering.

IP-level validation mandatory hai.

Example:

```
hostname
   |
   v
DNS
   |
   v
169.254.169.254
   |
   X
BLOCK
```

---

## 14. Reserved & Special IP Protection

Scanner ko special-purpose addresses bhi reject karne chahiye.

Examples include:

- unspecified addresses
- multicast addresses
- reserved addresses
- documentation/test ranges where applicable
- loopback
- link-local
- private addresses
- other non-public address categories

IP classification standard library ke reliable functionality par based
honi chahiye.

Manual string matching avoid karein.

Bad:

```python
if ip.startswith("10."):
    ...
```

Preferred:

```python
ipaddress.ip_address(value)
```

and proper network classification.

---

## 15. IPv4-Mapped IPv6 Protection

IPv4-mapped IPv6 addresses ko specially handle karna mandatory hai.

Example concept:

```
IPv6 representation
       |
       v
IPv4 mapped address
       |
       v
Original IPv4 classification
       |
       v
Security policy
```

Agar underlying IPv4 address private/loopback/link-local hai,
mapped IPv6 representation bhi reject honi chahiye.

---

## 16. DNS Rebinding Protection

DNS rebinding SSRF prevention ka critical part hai.

Unsafe flow:

```
Validate DNS
     |
     v
Public IP
     |
     v
DNS changes
     |
     v
Private IP
     |
     v
Request
```

Ye allowed nahi hona chahiye.

Safe architecture:

```
Resolve
   |
   v
Classify IP
   |
   v
Approved IP
   |
   v
Connect using validated result
```

DNS resolution aur actual connection ke beech destination ko
untrusted DNS lookup par depend nahi karna chahiye.

Implementation ko TOCTOU/DNS-rebinding risk minimize karna hoga.

---

## 17. Multiple DNS Records

A hostname multiple IPs resolve kar sakta hai.

Example:

```
example.com
     |
     +--> Public IP
     |
     +--> Public IP
     |
     +--> Private IP
```

Aise case mein scanner ko unsafe address ko ignore karke blindly kisi
address par connect nahi karna chahiye.

Security policy ke according resolution result evaluate hoga.

Default secure behavior:

Agar resolution set mein unsafe destination present hai aur connection
destination deterministic nahi hai, target ko reject karna preferred hai.

Implementation decision documented aur tested hona chahiye.

---

## 18. DNS Resolution Abstraction

DNS logic ko scanner code ke andar directly implement nahi karna.

Suggested structure:

```
app/
├── security/
│   ├── target_validator.py
│   ├── ip_classifier.py
│   ├── dns_resolver.py
│   └── network_policy.py
│
└── services/
    └── safe_http_client.py
```

Actual project structure Phase 01/02 architecture ke according adjust
ki ja sakti hai.

---

## 19. Target Validation Result

Validator ko structured result return karna chahiye.

Conceptual structure:

```
TargetValidationResult
├── valid
├── normalized_url
├── scheme
├── hostname
├── port
├── resolved_addresses
├── selected_address
├── reason
└── error_code
```

Exact implementation project coding standards ke according hogi.

---

## 20. Error Codes

Security failures machine-readable hone chahiye.

Example categories:

```
INVALID_URL
UNSUPPORTED_SCHEME
INVALID_HOSTNAME
URL_CREDENTIALS_NOT_ALLOWED
INVALID_PORT
DNS_RESOLUTION_FAILED
PRIVATE_IP_BLOCKED
LOOPBACK_BLOCKED
LINK_LOCAL_BLOCKED
METADATA_IP_BLOCKED
RESERVED_IP_BLOCKED
MULTICAST_IP_BLOCKED
UNSAFE_REDIRECT
DNS_REBINDING_DETECTED
NETWORK_POLICY_BLOCKED
```

Exact error taxonomy centralized honi chahiye.

---

## 21. Redirect Protection

Redirects SSRF protection bypass nahi kar sakte.

Example:

```
Public Target
     |
     v
HTTP 302
     |
     v
Private Target
     |
     X
BLOCK
```

Every redirect destination must pass through the same target validation
policy.

Scanner ko:

```
Target A
   |
   v
Redirect B
   |
   v
Validate B
   |
   v
Allow / Block
```

karna hoga.

Redirect validation bypass karna prohibited hai.

---

## 22. Redirect Limits

Redirect handling mein:

- maximum redirect count
- redirect timeout
- destination validation
- unsupported scheme rejection
- private IP rejection

mandatory hain.

Infinite redirect loops prevent hone chahiye.

---

## 23. Network Timeouts

Scanner ko unlimited network requests allow nahi karni.

Minimum timeout categories conceptually:

- DNS timeout
- Connect timeout
- Read timeout
- Overall request timeout

Exact values configuration se controlled honi chahiye.

Hardcoded values avoid karein.

---

## 24. Response Safety

Phase 03 scanner networking foundation provide karega.

Network client mein safety controls design hone chahiye:

- maximum response size
- request timeout
- redirect limit
- connection limit
- safe headers
- controlled HTTP methods

Large or malicious responses scanner resources exhaust nahi kar sakte.

---

## 25. HTTP Method Policy

Phase 03/04 scanner architecture mein default requests:

```
GET
HEAD
```

tak limited rakhna preferred hai.

Unsafe state-changing methods:

```
POST
PUT
PATCH
DELETE
```

scanner ke normal security audit flow mein use nahi hone chahiye.

---

## 26. SSRF Protection API

Suggested abstraction:

```
validate_target(url)
        |
        v
ValidatedTarget
        |
        v
safe_request(validated_target)
```

Not allowed:

```
http_client.get(user_url)
```

Allowed architecture:

```
user_url
   |
   v
validate_target()
   |
   v
ValidatedTarget
   |
   v
safe_request()
```

---

## 27. Safe HTTP Client

Suggested module:

```
app/services/safe_http_client.py
```

Responsibilities:

- accept only validated target objects
- enforce timeout policy
- enforce redirect policy
- enforce response limits
- prevent direct arbitrary URLs
- use controlled connection behavior
- provide consistent network errors
- produce structured results

The client must NOT accept an arbitrary raw URL from untrusted application
code without validation.

---

## 28. Separation of Responsibility

```
Target Validator
      |
      | validates destination
      v
Network Policy
      |
      | approves connection
      v
Safe HTTP Client
      |
      | performs request
      v
Scanner
```

Scanner ka responsibility:

Security configuration inspect karna.

Scanner ka responsibility nahi:

SSRF security policy independently decide karna.

---

## 29. Suggested Files

Phase 03 ke end tak project mein relevant files approximately:

```
app/
├── security/
│   ├── __init__.py
│   ├── target_validator.py
│   ├── ip_classifier.py
│   ├── dns_resolver.py
│   └── network_policy.py
│
├── services/
│   └── safe_http_client.py
│
└── schemas/
    └── target.py

tests/
└── security/
    ├── test_target_validator.py
    ├── test_ip_classifier.py
    ├── test_dns_resolver.py
    ├── test_network_policy.py
    └── test_safe_http_client.py
```

Exact paths may be adjusted according to Phase 01 architecture.

---

## 30. Configuration

Security-sensitive network settings must be configurable.

Examples:

```
ALLOWED_SCHEMES
ALLOWED_PORTS
DNS_TIMEOUT
CONNECT_TIMEOUT
READ_TIMEOUT
REQUEST_TIMEOUT
MAX_REDIRECTS
MAX_RESPONSE_SIZE
```

Secrets must never be stored in source code.

---

## 31. Logging

Security events should be logged.

Examples:

- Target validation failed
- Private IP blocked
- Loopback target blocked
- Metadata target blocked
- Unsafe redirect blocked
- DNS resolution failed
- Network policy rejected target

Logs should NOT contain:

- passwords
- authorization tokens
- cookies
- API keys
- sensitive credentials

---

## 32. Security Logging Example

Conceptual:

```
INFO  target_validation
      target=example.com
      result=allowed

WARN  target_validation
      reason=private_ip
      result=blocked
```

Do not log sensitive URL credentials or secret query parameters.

---

## 33. Test Strategy

Phase 03 testing is security-critical.

All validation rules must have automated tests.

### 33.1 Valid URL Tests

Test:

```
https://example.com
http://example.com
```

Expected:

```
VALID
```

### 33.2 Invalid Scheme Tests

Test:

```
file://...
ftp://...
gopher://...
javascript://...
unknown://...
```

Expected:

```
BLOCKED
```

### 33.3 Credential Tests

Test URLs containing:

- username
- password
- username:password

Expected:

```
BLOCKED
```

---

## 34. IP Security Tests

Test categories:

```
127.0.0.1
::1

10.x.x.x
172.16.x.x
192.168.x.x

169.254.x.x

169.254.169.254

IPv4-mapped IPv6

multicast

reserved
```

Every unsafe destination must be rejected.

---

## 35. DNS Tests

Mock DNS responses for:

- Public IP
- Private IP
- Loopback IP
- Multiple public IPs
- Public + private IP
- DNS failure
- Empty response
- IPv6 response

Tests must verify that policy decisions are deterministic.

---

## 36. DNS Rebinding Tests

Simulate:

```
Resolution #1
     |
     v
Public IP
```

followed by:

```
Resolution #2
     |
     v
Private IP
```

Expected:

```
BLOCK
```

Test the actual connection path as well as validator behavior.

---

## 37. Redirect Tests

Test:

```
Public -> Public
Public -> Private
Public -> Loopback
Public -> Metadata IP
Public -> Unsupported Scheme
```

Expected:

```
Public -> Public       ALLOW
Public -> Private     BLOCK
Public -> Loopback    BLOCK
Public -> Metadata    BLOCK
Unsupported Scheme    BLOCK
```

---

## 38. Timeout Tests

Mock slow network operations.

Verify:

- DNS timeout
- Connect timeout
- Read timeout
- Overall timeout

do not hang the application indefinitely.

---

## 39. Response Size Tests

Simulate responses exceeding configured limits.

Expected behavior:

```
Large Response
      |
      v
Limit exceeded
      |
      v
Request terminated safely
```

The application must remain stable.

---

## 40. Property-Based / Fuzz Testing

Where practical, target validation should be tested against malformed
and unusual URL inputs.

Examples:

- malformed hostnames
- unusual IPv6 representations
- encoded characters
- repeated separators
- invalid ports
- extremely long hostnames
- Unicode/IDN hostnames
- malformed schemes
- empty host
- whitespace
- control characters

Goal:

Invalid input must fail safely, never crash the application.

---

## 41. Security Test Rule

Never test SSRF protection against unauthorized real internal systems.

Use:

- Mocks
- Local test fixtures
- Controlled test networks
- Synthetic DNS responses
- Test HTTP servers

All testing must remain authorized and isolated.

---

## 42. API Integration

Phase 03 should expose target validation to later scan-management
components through an internal service interface.

Concept:

```
POST /scans
      |
      v
Scan Service
      |
      v
Target Validator
      |
      +---- BLOCK
      |
      v
Safe Target
      |
      v
Phase 04 Scanner
```

Phase 03 does not need to implement the complete /scans workflow.

That belongs to Phase 06.

---

## 43. Database Integration

Phase 03 may generate structured validation errors that Phase 06 can
persist with scan lifecycle information.

Phase 03 should NOT introduce unnecessary database tables.

Target security is primarily an application/network security boundary.

---

## 44. Performance Requirements

Target validation should be lightweight.

Avoid:

- repeated DNS lookups
- unnecessary network requests
- excessive retries
- uncontrolled redirects
- blocking operations without timeout

DNS caching may be introduced later only if it does not weaken security.

Security correctness has priority over micro-optimizations.

---

## 45. Failure Handling

Failures must be handled gracefully.

Example:

```
DNS Failure
    |
    v
Structured Error
    |
    v
Scan rejected / failed safely
```

Application crash:

```
DNS Failure
    |
    X
Application Crash
```

is not acceptable.

---

## 46. Security Invariants

The following invariants are mandatory:

**Invariant 1**  
No raw user URL reaches the network client.

**Invariant 2**  
Private IP addresses cannot be scanned.

**Invariant 3**  
Loopback addresses cannot be scanned.

**Invariant 4**  
Cloud metadata addresses cannot be scanned.

**Invariant 5**  
Redirect destinations are revalidated.

**Invariant 6**  
DNS results are security-classified before connection.

**Invariant 7**  
Network requests have bounded timeouts.

**Invariant 8**  
Network responses have bounded resource usage.

**Invariant 9**  
Credentials in target URLs are rejected.

**Invariant 10**  
Security validation cannot be bypassed by IPv6 representation tricks.

---

## 47. What NOT To Do

Do NOT:

- trust the hostname alone
- trust DNS without IP classification
- only block localhost
- only block 127.0.0.1
- only check IPv4
- ignore IPv6
- follow redirects without validation
- allow arbitrary ports
- allow arbitrary URL schemes
- accept URLs containing credentials
- perform unlimited retries
- perform unlimited redirects
- perform requests without timeouts
- let scanner modules bypass the safe HTTP client
- disable SSRF checks for convenience
- hardcode security exceptions
- log secrets

---

## 48. Code Quality Requirements

Implementation must follow:

- type hints
- clear naming
- small functions
- single responsibility
- centralized security policy
- structured exceptions
- testable abstractions
- dependency injection where useful
- no duplicated security logic

Avoid giant functions such as:

```
validate_and_resolve_and_connect_and_scan()
```

Instead separate responsibilities:

```
parse
  ↓
normalize
  ↓
validate
  ↓
resolve
  ↓
classify
  ↓
authorize
  ↓
connect
```

---

## 49. Acceptance Criteria

Phase 03 is accepted only when:

- [ ] HTTP/HTTPS validation works
- [ ] Invalid schemes are rejected
- [ ] Invalid hostnames are rejected
- [ ] URL credentials are rejected
- [ ] Port policy is enforced
- [ ] DNS resolution is controlled
- [ ] Private IPv4 is blocked
- [ ] Private IPv6 is blocked
- [ ] Loopback is blocked
- [ ] Link-local is blocked
- [ ] Metadata IP is blocked
- [ ] Reserved/multicast addresses are handled
- [ ] IPv4-mapped IPv6 is handled
- [ ] DNS rebinding protections are tested
- [ ] Redirects are validated
- [ ] Redirect limits exist
- [ ] Network timeouts exist
- [ ] Response size limits exist
- [ ] Safe HTTP client exists
- [ ] Scanner cannot bypass validation
- [ ] Security tests pass
- [ ] No secrets are logged
- [ ] Existing Phase 01/02 tests remain green

---

## 50. Definition of Done

Phase 03 is complete when:

```
URL
 |
 v
Validation
 |
 v
DNS
 |
 v
IP Security Check
 |
 v
Network Policy
 |
 v
Safe Target
 |
 v
Safe HTTP Client
```

works as one tested security boundary.

No Phase 04 scanner code should be required to implement SSRF protection.

---

## 51. Expected Deliverables

At the end of Phase 03:

- Target Validator
- IP Classifier
- DNS Resolver
- Network Policy
- Safe HTTP Client
- Security Exceptions
- Configuration
- Unit Tests
- Integration Tests
- Security Tests
- Documentation Updates

---

## 52. AI Coding Agent Prompt

Use the following prompt in the coding agent.

```
You are implementing PHASE 03 of the
AI-Powered Web Security Configuration Auditor.

Project:
AI-Powered Web Security Configuration Auditor

Stack:
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- MySQL
- HTML/CSS/Vanilla JS
- pytest
- HTTPX or the approved HTTP client

Read these documents before modifying code:

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

Your task is ONLY PHASE 03.

PRIMARY GOAL:

Implement a secure target validation and network safety boundary
that prevents SSRF and unsafe outbound connections.

MANDATORY RULE:

Never allow a raw user-controlled URL to directly reach the
HTTP/network client.

Required flow:

User URL
  -> Parse
  -> Normalize
  -> Validate
  -> DNS Resolve
  -> IP Classify
  -> Security Policy
  -> Safe Target
  -> Safe HTTP Client

IMPLEMENT:

1. URL parsing and normalization.
2. HTTP/HTTPS scheme validation.
3. Hostname validation.
4. Reject URLs containing credentials.
5. Port validation.
6. Controlled DNS resolution.
7. IPv4 classification.
8. IPv6 classification.
9. Private IP blocking.
10. Loopback blocking.
11. Link-local blocking.
12. Multicast blocking.
13. Reserved/special IP handling.
14. Cloud metadata IP blocking.
15. IPv4-mapped IPv6 protection.
16. DNS rebinding protection.
17. Redirect destination validation.
18. Maximum redirect count.
19. DNS/connect/read/request timeouts.
20. Maximum response size.
21. Safe HTTP client abstraction.
22. Centralized network security policy.
23. Structured security errors.
24. Comprehensive automated tests.

USE STANDARD LIBRARIES / TRUSTED LIBRARIES
FOR IP CLASSIFICATION.

Do not implement IP checks using simple string prefixes.

SECURITY REQUIREMENT:

The network client must accept a validated target abstraction
rather than an arbitrary raw URL wherever practical.

Redirects must pass through the same validation policy.

Do not trust hostname-only checks.

Do not assume that a public hostname always resolves to a public IP.

Handle IPv4, IPv6, and IPv4-mapped IPv6 safely.

Do not permit localhost, private networks, link-local addresses,
loopback addresses, multicast, reserved unsafe destinations,
or cloud metadata addresses.

TEST USING MOCKS AND CONTROLLED FIXTURES.

Do not perform unauthorized scans against real internal infrastructure.

TEST:

- valid HTTP URL
- valid HTTPS URL
- invalid schemes
- malformed URLs
- credentials in URL
- invalid ports
- localhost
- 127.0.0.1
- ::1
- private IPv4
- private IPv6
- link-local
- metadata IP
- multicast
- reserved addresses
- IPv4-mapped IPv6
- DNS failures
- multiple DNS records
- public + private DNS results
- DNS rebinding simulation
- safe redirect
- unsafe redirect
- metadata redirect
- timeout
- oversized response
- malformed/unusual URLs

DO NOT IMPLEMENT:

- TLS scanning
- certificate analysis
- HTTP header scanning
- security findings
- risk scoring
- AI explanation
- dashboard
- reporting
- full scan orchestration

Those belong to later phases.

PRESERVE EXISTING FUNCTIONALITY.

Do not rewrite Phase 01 or Phase 02 unnecessarily.

Do not modify database schema unless absolutely required by the
existing architecture.

Do not introduce new frameworks.

Do not hardcode secrets.

Do not disable security checks for development convenience.

After implementation:

1. Run formatting/linting if configured.
2. Run all Phase 03 tests.
3. Run all existing project tests.
4. Fix regressions.
5. Verify application startup.
6. Verify imports.
7. Verify type correctness where tooling exists.
8. Report changed files.
9. Report tests executed and results.
10. Report any unresolved issues.

Do not claim completion without actually running the tests.

The implementation must be production-oriented, secure,
maintainable, and consistent with the existing architecture.
```

---

## 53. Phase Completion Record

After implementation, update this section:

```
Phase: 03
Status: Completed / Pending

Implemented:
- Target validation
- DNS security
- IP classification
- SSRF protection
- Redirect protection
- Safe HTTP client
- Timeout/resource controls

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
Phase 04 — Core Security Scanner
```

---

## 54. Transition To Phase 04

Once Phase 03 is complete, the project will have a trusted and secure
network access layer.

The next phase will build the actual security scanner on top of it.

Expected architecture:

```
User Target
    |
    v
Phase 03
Security Boundary
    |
    v
Safe Network Access
    |
    v
Phase 04
Security Scanner
    |
    v
TLS + HTTP Checks
    |
    v
Raw Findings
```

### Phase 04 Focus

The next phase will implement deterministic security checks for:

- TLS configuration
- certificate properties
- protocol versions
- cipher/security configuration
- HTTP security headers
- cookies
- HSTS
- redirect behavior
- other security controls defined in
  `Docs/SCANNER_SPECIFICATION.md`

The scanner must treat Phase 03's safe networking layer as mandatory.

---

### FINAL PHASE 03 PRINCIPLE

The scanner must never become an SSRF proxy.

Every outbound destination must be validated, classified,
authorized, and bounded before network access is permitted.