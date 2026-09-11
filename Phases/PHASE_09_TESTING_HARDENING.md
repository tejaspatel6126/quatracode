# PHASE 09 — TESTING & SECURITY HARDENING

## 1. Phase Overview

**Phase Name:** Testing & Security Hardening
**Phase Number:** 09
**Project:** AI-Powered Web Security Configuration Auditor
**Status:** Planned
**Depends On:** Phases 01–08

---

## 2. Objective

The objective of Phase 09 is to perform comprehensive testing, security
validation, performance verification, regression testing, and final
application hardening before integration, demonstration, and deployment.

This phase must verify that the system is:

- Functionally correct
- Secure by design
- Resistant to common application attacks
- Resistant to SSRF bypass attempts
- Deterministic in security findings
- Deterministic in risk scoring
- Reliable when external services fail
- Safe under concurrent usage
- Safe under malformed input
- Production-ready from a testing perspective

No major new product feature should be introduced during this phase.

---

## 3. Phase Scope

Phase 09 covers:

1. Unit testing
2. Integration testing
3. API testing
4. End-to-end testing
5. Database testing
6. Scanner testing
7. SSRF security testing
8. Authentication testing
9. Authorization testing
10. Frontend security testing
11. AI security testing
12. Performance testing
13. Concurrency testing
14. Failure and recovery testing
15. Dependency security checks
16. Static analysis
17. Secret scanning
18. Regression testing
19. Security hardening
20. Release readiness verification

---

## 4. Testing Architecture

The testing strategy should follow a layered approach:

```
             E2E Tests
                |
          Integration
                |
        +-------+-------+
        |       |       |
       API     DB     Scanner
        |       |       |
        +-------+-------+
                |
           Unit Tests
```

Security testing must exist across all layers.

---

## 5. Test Environments

Use separate environments where practical.

```
Development
     |
     v
Testing
     |
     v
Staging
     |
     v
Production
```

Production data must never be used for destructive tests.

Recommended test environments:

- Local development
- Automated test environment
- Controlled staging environment

---

## 6. Test Data Policy

Testing must use synthetic or controlled data.

Do not use:

- Real user passwords
- Real API keys
- Real private keys
- Production database dumps
- Sensitive customer information
- Unauthorized external targets

Security scanner testing must use authorized targets only.

---

## 7. Unit Testing

Unit tests must cover individual components independently.

**Required areas:**

**Core**
- Configuration
- Validation helpers
- Security utilities
- Error handling
- Logging helpers

**Target Security**
- URL normalization
- Scheme validation
- Host validation
- IP validation
- DNS resolution
- Private address detection
- Redirect validation

**Scanner**
- TLS checks
- Certificate checks
- HTTP checks
- Header checks
- Cookie checks

**Finding Engine**
- Finding creation
- Severity assignment
- Evidence generation
- Deduplication

**Risk Engine**
- Risk calculation
- Severity weighting
- Score boundaries
- Deterministic output

**AI**
- Prompt construction
- Redaction
- Output validation
- Provider abstraction
- Fallback handling

---

## 8. Deterministic Scanner Tests

Scanner tests must use fixed controlled fixtures.

For the same target state:

```
Target Configuration
        |
        v
     Scanner
        |
        v
    Same Findings
```

Repeated scans against the same controlled fixture should produce equivalent
security findings.

Tests must verify:

- Expected findings appear
- Unexpected findings do not appear
- Evidence is correctly associated
- Severity is correct
- Duplicate findings are handled correctly

---

## 9. TLS Testing

Test TLS-related behavior including:

- Valid certificate
- Expired certificate
- Hostname mismatch
- Invalid certificate chain
- Weak protocol configuration
- Secure protocol configuration
- TLS handshake failure
- Connection timeout
- Certificate parsing failure

The scanner must fail safely when TLS communication cannot be completed.

---

## 10. HTTP Security Testing

Test security-header behavior for:

- HSTS
- Content-Security-Policy
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- X-Frame-Options
- Cookie attributes
- HTTPS enforcement

Each test must verify the exact rule defined in:

`Docs/SCANNER_SPECIFICATION.md`

The test suite must not invent security rules that are not part of the
documented specification.

---

## 11. SSRF Security Testing

SSRF protection is one of the most critical parts of the system.

Test target validation against applicable:

- localhost
- loopback IPv4
- loopback IPv6
- private IPv4 ranges
- private IPv6 ranges
- link-local addresses
- cloud metadata addresses
- IPv4-mapped IPv6 addresses
- unsafe schemes
- disallowed ports
- malformed URLs

Example:

```
User Input
    |
    v
Target Validator
    |
    +---- Safe ----> Scanner
    |
    +---- Unsafe --> BLOCK
```

---

## 12. DNS Security Testing

Test DNS-related edge cases including:

- Hostname resolving to public IP
- Hostname resolving to private IP
- Hostname resolving to loopback
- Multiple DNS records
- IPv4 and IPv6 results
- DNS resolution failure
- Resolution timeout
- DNS changes between validation and connection

The implementation must follow the SSRF controls defined in
`Docs/SECURITY.md`.

---

## 13. Redirect Security Testing

Test redirects such as:

```
Public URL
    |
    v
Public URL
    |
    v
Allowed
```

and:

```
Public URL
    |
    v
Private Address
    |
    X
Blocked
```

Verify that redirect destinations cannot bypass target validation.

Test:

- HTTP to HTTPS
- HTTPS to HTTP
- Public to private
- Public to loopback
- Multiple redirects
- Redirect loops
- Invalid redirect URLs
- Excessive redirect chains

---

## 14. Request Security Testing

Verify protections for:

- Request timeouts
- Connection timeouts
- Read timeouts
- Maximum response size
- Maximum redirect count
- Maximum scan duration
- Maximum concurrent scans
- Unsupported content types
- Malformed responses

The scanner must terminate safely when limits are reached.

---

## 15. Authentication Testing

Test:

- Valid login
- Invalid login
- Missing credentials
- Expired authentication
- Logout
- Protected endpoints
- Unauthenticated API access
- Authentication state handling

Expected:

```
Authenticated
     |
     v
Allowed

Unauthenticated
     |
     v
Rejected
```

---

## 16. Authorization Testing

Test resource ownership carefully.

Example:

```
User A
  |
  +--> Own Scan ------> ALLOWED
  |
  +--> User B Scan ---> DENIED
```

Test for:

- IDOR
- Scan ownership bypass
- Finding ownership bypass
- Report ownership bypass
- Administrative endpoint access
- Privilege escalation

Changing a resource ID in an API request must never bypass authorization.

---

## 17. API Security Testing

Test:

- Invalid JSON
- Missing fields
- Extra fields
- Incorrect data types
- Oversized requests
- Invalid URLs
- Invalid IDs
- Invalid pagination
- Invalid query parameters
- Authentication failures
- Authorization failures
- Rate limits

The API must return safe, predictable responses.

---

## 18. SQL Injection Testing

All database operations must use parameterized queries or ORM-safe
operations.

Test malicious input in:

- User fields
- Target URL fields
- Search parameters
- Pagination parameters
- Scan IDs
- Filtering parameters

Expected result:

```
Malicious Input
      |
      v
Validation / ORM
      |
      v
No SQL Execution
```

No raw string concatenation should be used for SQL construction.

---

## 19. XSS Testing

Test user-controlled values such as:

- Target URL
- Finding title
- Finding description
- Evidence
- AI-generated explanation
- Report content
- User-provided metadata

The frontend must render untrusted content safely.

Prefer:

```js
element.textContent = value;
```

instead of unsafe HTML injection.

---

## 20. Frontend Security Testing

Verify:

- XSS protection
- Safe API response rendering
- Safe URL rendering
- Authentication handling
- Session expiration
- Error handling
- No sensitive data in browser storage unless required
- No hardcoded secrets
- No exposed internal endpoints

The frontend must never make security decisions that belong to the backend.

---

## 21. AI Security Testing

AI is an untrusted external component.

**Test: Prompt Injection**

Attempt to inject instructions through:

- Finding descriptions
- Target metadata
- HTTP headers
- Server responses
- Certificate metadata
- Other scanner-controlled text

The AI prompt must maintain system authority.

**Output Validation**

Test:

- Invalid JSON
- Missing fields
- Unexpected fields
- Excessive output
- Malformed output
- Untrusted HTML
- Unsupported claims

**AI Boundary**

Verify that AI cannot change:

- Finding severity
- Risk score
- Finding existence
- Scan status

---

## 22. AI Redaction Testing

Verify that sensitive information is removed before AI processing.

Potential sensitive values include:

- Authorization headers
- Cookies
- API tokens
- Passwords
- Private keys
- Session identifiers
- Secrets

Example:

```
Raw Finding
    |
    v
Redaction
    |
    v
Safe AI Input
```

Tests must confirm that known secret patterns are not sent to the AI layer.

---

## 23. AI Failure Testing

Simulate:

- Provider timeout
- Provider unavailable
- Authentication failure
- Rate limit
- Invalid provider response
- Malformed AI output
- Network failure

Expected behavior:

```
AI Failure
    |
    v
Deterministic Explanation
    |
    v
Scan Remains Successful
```

AI failure must not invalidate the security scan.

---

## 24. Database Testing

Test:

- Database connection
- Model creation
- Relationships
- Foreign keys
- Constraints
- Unique indexes
- Query filtering
- Pagination
- Transactions
- Rollbacks
- Migration upgrades
- Migration consistency

Test failure scenarios such as:

- Database unavailable
- Transaction failure
- Connection timeout
- Constraint violation

---

## 25. Migration Testing

Test:

```
Empty Database
      |
      v
alembic upgrade head
      |
      v
Current Schema
```

Also verify that migrations are reproducible from a clean database.

Migration files must remain committed to source control.

---

## 26. API Integration Testing

Test the complete API workflow:

```
Login
  |
Create Scan
  |
Get Status
  |
Get Results
  |
Get Findings
  |
Get Risk
  |
Get AI Explanation
```

Verify that returned data matches the database and deterministic security
engine results.

---

## 27. End-to-End Testing

At least one complete automated E2E scenario should verify:

```
Login
  |
Dashboard
  |
Submit Target
  |
Scan
  |
Results
  |
Finding
  |
Risk
  |
AI Explanation
  |
Report
```

The E2E test should use a controlled test target.

---

## 28. Scan Lifecycle Testing

Verify valid transitions:

```
QUEUED
  |
RUNNING
  |
COMPLETED
```

Failure:

```
QUEUED
  |
RUNNING
  |
FAILED
```

Cancellation:

```
QUEUED/RUNNING
      |
      v
  CANCELLED
```

Invalid state transitions must be rejected.

---

## 29. Concurrency Testing

Run multiple controlled scans simultaneously.

Example:

```
Scan A ----+
Scan B ----+--> Scan Manager
Scan C ----+
```

Verify:

- Correct scan ownership
- No shared-state corruption
- No database race conditions
- Correct statuses
- Correct findings
- Correct risk scores
- Resource limits

---

## 30. Rate Limiting Tests

Verify rate limits for:

- Login
- Scan creation
- Expensive endpoints
- AI requests where applicable

Expected:

```
Normal Usage
    |
    v
Allowed

Excessive Usage
    |
    v
Rate Limited
```

Rate limits must not be implemented in a way that allows trivial bypasses.

---

## 31. Resource Limit Testing

Test limits for:

- Request body size
- Response size
- Scan duration
- Connection timeout
- Redirect count
- Concurrent scans
- AI token/output limits

A malicious or broken target must not consume unlimited application
resources.

---

## 32. Error Handling Testing

Verify that internal errors are not exposed to users.

**Bad:**

```
Database password...
Python traceback...
Internal file path...
```

**Good:**

```
The requested operation could not be completed.
Request ID: <request-id>
```

Detailed diagnostics may remain in protected server logs.

---

## 33. Logging Security Testing

Review logs for accidental leakage of:

- Passwords
- API keys
- Authorization headers
- Cookies
- Tokens
- Private keys
- Sensitive request data

Logs should contain useful security context without exposing secrets.

---

## 34. Security Headers Testing

Verify production responses contain the intended security headers.

Test:

- Content-Security-Policy
- X-Content-Type-Options
- Referrer-Policy
- HSTS where HTTPS is enabled
- Other documented headers

Only headers defined by the project security policy should be treated as
required acceptance criteria.

---

## 35. CORS Testing

Verify:

- Allowed origins work
- Unauthorized origins are rejected
- Wildcard origins are not used unnecessarily
- Credential handling is correct
- Development origins do not accidentally remain in production

---

## 36. Performance Testing

Measure:

- API response latency
- Scan startup latency
- Scan completion time
- Database query latency
- Concurrent scan throughput
- Memory usage
- CPU usage

Performance testing should use controlled targets and predictable test data.

---

## 37. Performance Acceptance

The system should remain responsive under expected hackathon/demo usage.

Performance problems must be investigated when they result from:

- Unbounded queries
- Missing indexes
- Excessive database calls
- Uncontrolled concurrency
- Unbounded scanner operations
- Excessive AI calls

Do not remove security controls simply to improve benchmark numbers.

---

## 38. Failure and Recovery Testing

Simulate:

- Database unavailable
- Scanner timeout
- Target unavailable
- TLS handshake failure
- HTTP connection failure
- AI provider failure
- Worker restart
- Network interruption

The application must fail safely and maintain consistent scan state.

---

## 39. Dependency Security

Review all project dependencies.

Check for:

- Known vulnerabilities
- Unnecessary packages
- Outdated critical libraries
- Unused dependencies

Only required dependencies should remain in the production environment.

---

## 40. Static Analysis

Run available:

- Python linting
- Formatting checks
- Static analysis
- Type checking
- JavaScript linting where configured
- Security analysis

All critical findings must be resolved before release.

---

## 41. Secret Scanning

Perform repository-wide secret scanning.

Search for accidental:

- API keys
- Passwords
- Tokens
- Private keys
- Database credentials
- Cloud credentials

Verify:

- `.env`
- `*.pem`
- `*.key`
- credentials
- secrets

and other sensitive files are appropriately excluded from source control.

---

## 42. Git Repository Review

Before release:

```
git status
git diff
git log
```

Verify:

- No debug code
- No temporary files
- No secrets
- No local database files
- No generated cache files
- No accidental credentials
- No test bypasses

---

## 43. Regression Testing

Every important existing feature must continue working after hardening.

Regression areas:

- Authentication
- Target validation
- Scanner
- Findings
- Risk
- Database
- API
- Frontend
- AI
- Reports

No security fix should silently break unrelated functionality.

---

## 44. Security Regression Tests

Every discovered security bug should result in a permanent regression test.

Example:

```
Security Bug
    |
    v
Fix
    |
    v
Regression Test
    |
    v
Permanent Protection
```

This prevents the same vulnerability from returning in future changes.

---

## 45. Test Automation

Tests should be executable through a simple command.

Example:

```
pytest
```

Where configured, additional checks may include:

```
ruff check .
ruff format --check .
```

The exact commands must match the project's dependency configuration.

---

## 46. CI Validation

If CI is configured, the pipeline should execute:

```
Install
   |
Lint
   |
Unit Tests
   |
Integration Tests
   |
Security Checks
   |
Build
```

A release build should fail when critical tests fail.

---

## 47. Controlled Security Targets

Create controlled fixtures for testing.

Possible fixtures:

- secure-target
- missing-headers-target
- weak-tls-target
- invalid-cert-target
- redirect-target
- large-response-target
- slow-response-target

These targets must be isolated and intentionally created for testing.

---

## 48. No Unauthorized Scanning

The testing phase must not scan random third-party websites.

Use only:

- Local test servers
- Test containers
- Intentionally configured fixtures
- Authorized public security testing targets

The project's purpose is defensive security auditing.

---

## 49. Security Hardening Checklist

**Backend**
- [ ] Input validation enabled
- [ ] SSRF validation enforced
- [ ] Redirect validation enforced
- [ ] Timeouts configured
- [ ] Resource limits configured
- [ ] Rate limiting configured
- [ ] Authentication protected
- [ ] Authorization enforced
- [ ] Safe error responses
- [ ] Secure logging

**Database**
- [ ] Parameterized queries
- [ ] Least-privilege database user
- [ ] Foreign keys verified
- [ ] Indexes verified
- [ ] Migrations verified
- [ ] Backup strategy verified

**Frontend**
- [ ] XSS-safe rendering
- [ ] No secrets
- [ ] Safe URL handling
- [ ] Authentication handling
- [ ] Error handling
- [ ] CSP compatibility

**AI**
- [ ] Input redaction
- [ ] Prompt injection defenses
- [ ] Output validation
- [ ] Token limits
- [ ] Timeout
- [ ] Failure fallback
- [ ] No authority over findings/risk

---

## 50. Final Test Matrix

| Area | Required |
|---|---|
| Unit Tests | PASS |
| Integration Tests | PASS |
| API Tests | PASS |
| E2E Tests | PASS |
| Database Tests | PASS |
| Scanner Tests | PASS |
| SSRF Tests | PASS |
| Auth Tests | PASS |
| Authorization Tests | PASS |
| Frontend Security | PASS |
| AI Security | PASS |
| Performance | PASS |
| Regression | PASS |
| Dependency Review | PASS |
| Secret Scan | PASS |

Critical failures must block release.

---

## 51. AI Coding Agent Prompt

Use the following prompt when implementing Phase 09:

```
You are a senior QA engineer, application security engineer,
penetration-testing defensive specialist, backend engineer, frontend
engineer, and DevOps engineer.

You are working on:

AI-Powered Web Security Configuration Auditor

Implement PHASE 09 — TESTING & SECURITY HARDENING.

IMPORTANT:
This phase focuses on testing and hardening the existing implementation.

DO NOT introduce major new product features.

==================================================
DOCUMENTS TO FOLLOW
==================================================

Read and follow:

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

Also inspect:

Phases/PHASE_01_FOUNDATION.md
Phases/PHASE_02_DATABASE.md
Phases/PHASE_03_TARGET_SECURITY.md
Phases/PHASE_04_SCANNER.md
Phases/PHASE_05_FINDING_RISK.md
Phases/PHASE_06_API_SCAN_MANAGER.md
Phases/PHASE_07_FRONTEND.md
Phases/PHASE_08_AI.md

==================================================
PRIMARY OBJECTIVE
==================================================

Make the existing system thoroughly tested and security hardened.

Test:

- Backend
- Database
- Scanner
- Target validation
- SSRF protection
- Finding engine
- Risk engine
- API
- Authentication
- Authorization
- Frontend
- AI
- Reports
- Error handling
- Concurrency
- Performance

==================================================
SECURITY REQUIREMENT
==================================================

This project is a defensive web security auditing system.

Do not add offensive capabilities.

Do not implement:

- Exploitation
- Brute force
- Credential attacks
- Unauthorized scanning
- Malware
- Payload delivery

All scanner testing must use controlled or explicitly authorized targets.

==================================================
SSRF TESTING
==================================================

Thoroughly test:

- localhost
- loopback
- private IPv4
- private IPv6
- link-local
- cloud metadata
- IPv4-mapped IPv6
- unsafe schemes
- unsafe ports
- DNS resolution edge cases
- unsafe redirects
- redirect loops

Do not weaken SSRF protection to make tests pass.

==================================================
DETERMINISTIC ENGINE RULE
==================================================

Finding generation and risk scoring are authoritative.

Tests must verify that:

Same scanner input
        =
Same findings
        =
Same severity
        =
Same risk score

AI must not affect these values.

==================================================
AI SECURITY
==================================================

Test:

- Prompt injection
- Sensitive data redaction
- Malformed provider output
- Provider timeout
- Provider failure
- Rate limiting
- Token limits
- Output validation

AI must remain explanation-only.

==================================================
DATABASE SECURITY
==================================================

Verify:

- Parameterized queries
- ORM safety
- Authorization filters
- Transactions
- Rollbacks
- Constraints
- Indexes
- Migrations

Test IDOR and cross-user data access.

==================================================
FRONTEND SECURITY
==================================================

Test:

- XSS
- Unsafe HTML rendering
- URL handling
- Authentication
- API errors
- Session expiration

Use safe DOM APIs such as textContent where appropriate.

==================================================
PERFORMANCE
==================================================

Test:

- API latency
- Scan duration
- Concurrent scans
- Database performance
- Resource limits
- Memory usage
- CPU usage

Do not remove security controls to improve performance.

==================================================
FAILURE TESTING
==================================================

Simulate:

- Database unavailable
- Target unavailable
- TLS failure
- HTTP failure
- Timeout
- AI provider failure
- Malformed responses
- Worker restart

The application must fail safely.

==================================================
REPOSITORY SAFETY
==================================================

Before completion:

- Search for secrets
- Review git diff
- Review git status
- Remove debug code
- Remove temporary files
- Verify .gitignore
- Verify no credentials are committed

==================================================
TEST EXECUTION
==================================================

Run the complete test suite.

Run all configured:

- Unit tests
- Integration tests
- API tests
- E2E tests
- Security tests
- Database tests
- Frontend tests
- AI tests
- Performance tests
- Regression tests
- Static analysis
- Dependency checks
- Secret scanning

Fix failures without weakening security.

==================================================
IMPORTANT
==================================================

Do not rewrite working architecture unnecessarily.

Preserve existing functionality.

Do not duplicate business logic.

Do not change documented scanner behavior without updating the appropriate
specification and tests.

Do not claim completion if critical security tests are failing.

==================================================
FINAL REPORT
==================================================

At the end provide:

1. Files changed
2. Tests added
3. Tests executed
4. Test results
5. Security vulnerabilities discovered
6. Security fixes implemented
7. Performance observations
8. Remaining risks
9. Known limitations
10. Release readiness status

Also update the Phase 09 completion record.
```

---

## 52. Acceptance Criteria

Phase 09 is complete only when:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] E2E tests pass
- [ ] Database tests pass
- [ ] Scanner tests pass
- [ ] TLS tests pass
- [ ] HTTP security tests pass
- [ ] SSRF tests pass
- [ ] Redirect security tests pass
- [ ] Authentication tests pass
- [ ] Authorization tests pass
- [ ] IDOR tests pass
- [ ] SQL injection tests pass
- [ ] XSS tests pass
- [ ] AI security tests pass
- [ ] AI fallback tests pass
- [ ] Concurrency tests pass
- [ ] Resource-limit tests pass
- [ ] Performance tests pass
- [ ] Regression tests pass
- [ ] Dependency review completed
- [ ] Secret scanning completed
- [ ] Static analysis completed
- [ ] Production security configuration reviewed
- [ ] No critical unresolved security issue remains

---

## 53. Definition of Done

Phase 09 is considered DONE when:

- The complete automated test suite passes.
- Critical security controls have dedicated tests.
- SSRF protection has been tested against major bypass categories.
- Authentication and authorization have been tested.
- IDOR protection has been verified.
- Scanner behavior is deterministic.
- Risk scoring is deterministic.
- AI cannot alter authoritative security results.
- AI failure does not break scanning.
- Database integrity is verified.
- Frontend security is verified.
- Resource limits are verified.
- Performance is acceptable for the intended workload.
- No secrets are present in the repository.
- Security regressions are covered by permanent tests.
- The system is ready for final integration and deployment.

---

## 54. Phase Completion Record

After successful implementation, update this section:

```
Phase: 09
Status: COMPLETED
Implementation Date: YYYY-MM-DD

Tests:
- Total:
- Passed:
- Failed:
- Skipped:

Security Tests:
- SSRF: PASS
- Redirect Security: PASS
- Authentication: PASS
- Authorization: PASS
- IDOR: PASS
- SQL Injection: PASS
- XSS: PASS
- AI Security: PASS
- Secret Scan: PASS

Performance:
- Status: PASS / NEEDS REVIEW

Regression:
- Status: PASS / NEEDS REVIEW

Critical Issues:
- None / ...

Release Readiness:
- READY / NOT READY

Next Phase:
Phase 10 — Integration, Demo & Deployment
```

---

## 55. Final Principle

Phase 09 must prove that the system is not merely functional but secure,
predictable, and reliable.

The most important validation chain is:

```
Input
  |
Validation
  |
Secure Scan
  |
Deterministic Findings
  |
Deterministic Risk
  |
Safe AI Explanation
  |
Verified Output
```

Security controls must never be weakened simply to make tests pass.

The objective is not:

> "The application works."

The objective is:

> "The application works correctly, fails safely, and remains secure under
> expected misuse and failure conditions."