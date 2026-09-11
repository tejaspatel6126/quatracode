# PHASE 10 — INTEGRATION, DEMO & DEPLOYMENT

## 1. Phase Overview

**Phase Name:** Integration, Demo & Deployment
**Phase Number:** 10
**Project:** AI-Powered Web Security Configuration Auditor
**Status:** Planned
**Depends On:** Phases 01–09

---

## 2. Objective

The objective of Phase 10 is to integrate the complete application, perform
final end-to-end validation, prepare the controlled hackathon demonstration,
and deploy the application in a secure production-like environment.

After Phase 10, the project should operate as one complete security auditing
platform rather than a collection of independent modules.

The final system must support:

- User authentication
- Secure target submission
- SSRF protection
- TLS/SSL analysis
- HTTP security analysis
- Finding generation
- Deterministic severity classification
- Deterministic risk scoring
- Scan lifecycle management
- Database persistence
- REST APIs
- Web dashboard
- AI-powered explanations
- Security reports
- Logging
- Monitoring
- Production deployment
- Controlled demonstration

---

## 3. Phase Scope

Phase 10 covers:

1. Complete module integration
2. End-to-end workflow validation
3. Production configuration
4. Deployment configuration
5. Infrastructure verification
6. Final security verification
7. Demo environment preparation
8. Demo rehearsal
9. Final documentation verification
10. Release preparation

No major new security detection feature should be introduced during this
phase.

---

## 4. Final Application Architecture

The final application should follow this architecture:

```
User
 |
 v
Frontend
 |
 v
FastAPI
 |
 +--> Authentication
 |
 +--> Target Validation
 |
 +--> Scan Manager
        |
        v
      Scanner
        |
        v
     Findings
        |
        v
    Risk Engine
        |
        v
     Database
        |
        v
  AI Explanation
        |
        v
    Frontend
```

The deterministic security engine remains authoritative.

---

## 5. Complete Scan Pipeline

The final scan pipeline must be:

```
Target URL
    |
    v
Normalize
    |
    v
Validate
    |
    v
SSRF Protection
    |
    v
TLS Analysis
    |
    v
HTTP Analysis
    |
    v
Findings
    |
    v
Risk Score
    |
    v
Persist Results
    |
    v
AI Explanation
    |
    v
Report
```

Every stage must use the existing implementation from Phases 01–09.

Do not duplicate security logic inside API routes or frontend code.

---

## 6. Integration Requirements

All major modules must be integrated successfully:

```
Phase 01 -> Foundation
Phase 02 -> Database
Phase 03 -> Target Security
Phase 04 -> Scanner
Phase 05 -> Finding/Risk
Phase 06 -> API/Scan Manager
Phase 07 -> Frontend
Phase 08 -> AI
Phase 09 -> Testing/Hardening
Phase 10 -> Integration/Deployment
```

Each phase must remain compatible with the documented architecture.

---

## 7. Application Startup

Verify that the application starts correctly.

Development example:

```
uvicorn app.main:app --reload
```

Production architecture:

```
Internet
   |
 Nginx
   |
 HTTPS
   |
Gunicorn
   |
Uvicorn
   |
FastAPI
```

Development-only settings must not be enabled in production.

---

## 8. Environment Configuration

All environment-specific values must be provided through environment
variables.

Expected configuration categories include:

- `APPLICATION_ENV`
- `SECRET_KEY`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `AI_ENABLED`
- `AI_PROVIDER`
- `AI_MODEL`
- `AI_API_KEY`
- `AI_TIMEOUT`
- `AI_MAX_TOKENS`
- `LOG_LEVEL`

Never hardcode:

- Passwords
- API keys
- Tokens
- Database credentials
- Private keys
- Production secrets

The repository should contain:

```
.env.example
```

but must not contain real credentials.

---

## 9. Database Deployment

Before deployment:

- Verify database connectivity.
- Verify migration history.
- Apply migrations.
- Verify required tables.
- Verify indexes.
- Verify foreign keys.
- Verify constraints.
- Verify database permissions.
- Verify connection pooling.
- Verify backup configuration.

Example:

```
alembic upgrade head
```

Production schema changes must be performed through migrations.

---

## 10. Database Backup

A production-like deployment must have a backup strategy.

Verify:

- Backup creation
- Backup storage
- Backup retention
- Database restoration
- Recovery documentation

A backup should be considered valid only after restoration has been tested.

---

## 11. Authentication Integration

Verify the complete authentication flow:

```
Login
  |
  v
Authentication
  |
  v
Session / Token
  |
  v
Protected APIs
```

Verify:

- Valid login
- Invalid login
- Logout
- Expired authentication
- Protected routes
- Authentication failures

---

## 12. Authorization Integration

Every user-owned resource must enforce ownership.

Example:

```
User A
 |
 +--> Scan A --> ALLOWED
 |
 +--> Scan B --> DENIED
```

Verify ownership for:

- Scans
- Findings
- Risk results
- Reports
- AI explanations

Changing a resource ID must never bypass authorization.

---

## 13. Target Validation Integration

Target validation must occur before any network operation.

Required sequence:

```
Input
 |
 v
Normalization
 |
 v
Scheme Check
 |
 v
Host Check
 |
 v
DNS Validation
 |
 v
IP Validation
 |
 v
SSRF Validation
 |
 v
Scanner
```

The scanner must never independently bypass the target-security service.

---

## 14. SSRF Final Verification

The final deployment must continue blocking applicable:

- Localhost
- Loopback IPv4
- Loopback IPv6
- Private IPv4
- Private IPv6
- Link-local addresses
- Cloud metadata endpoints
- IPv4-mapped IPv6 addresses
- Unsafe schemes
- Disallowed ports
- Unsafe redirect destinations

Example:

```
User Target
    |
    v
Validator
    |
    +---- Safe ----> Scanner
    |
    +---- Unsafe --> BLOCK
```

---

## 15. Redirect Protection

Redirect destinations must be validated.

Example:

```
Public URL
    |
    v
Redirect
    |
    v
Private IP
    |
    X
Blocked
```

Test:

- HTTP -> HTTPS
- HTTPS -> HTTP
- Public -> private
- Public -> localhost
- Multiple redirects
- Redirect loops
- Invalid redirects

---

## 16. Scanner Integration

The scanner must perform only the documented security checks.

**TLS checks may include:**

- Certificate validity
- Certificate expiration
- Hostname verification
- Certificate chain
- TLS protocol configuration
- Other documented TLS rules

**HTTP checks may include:**

- HSTS
- CSP
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- X-Frame-Options
- Cookie security attributes
- Other documented HTTP rules

All rules must follow:

`Docs/SCANNER_SPECIFICATION.md`

---

## 17. Finding Engine Integration

Scanner results must be passed to the deterministic finding engine.

```
Scanner
   |
   v
Finding Engine
   |
   v
Finding Objects
   |
   v
Database
```

The finding engine determines:

- Finding existence
- Finding category
- Severity
- Evidence
- Remediation reference

AI must not determine these values.

---

## 18. Risk Engine Integration

Risk calculation must remain deterministic.

```
Findings
   |
   v
Risk Engine
   |
   v
Risk Score
```

Identical inputs must produce identical scores.

The risk score must not depend on:

- AI output
- AI model
- AI provider
- AI availability
- AI wording

---

## 19. AI Integration

AI should operate after deterministic findings and risk calculation.

```
Findings
   |
   v
Redaction
   |
   v
AI Provider
   |
   v
Validation
   |
   v
Explanation
```

AI must only explain existing findings.

AI must never:

- Create authoritative findings
- Change severity
- Change risk score
- Change scan status
- Bypass SSRF
- Bypass authorization
- Execute remediation

---

## 20. AI Failure Handling

The application must remain functional when AI is unavailable.

Example:

```
AI Available
     |
     v
AI Explanation

AI Unavailable
     |
     v
Deterministic Explanation
```

AI provider failure must not cause a completed security scan to become a
failed security scan.

---

## 21. API Integration

Verify the complete API workflow:

```
POST /auth/login
      |
      v
POST /scans
      |
      v
GET /scans/{id}
      |
      v
GET /scans/{id}/findings
      |
      v
GET /scans/{id}/risk
      |
      v
GET /scans/{id}/ai
```

The exact endpoint paths must follow:

`Docs/API.md`

Do not introduce conflicting duplicate endpoints.

---

## 22. Scan Lifecycle

Verify:

```
QUEUED
  |
  v
RUNNING
  |
  v
COMPLETED
```

Failure:

```
QUEUED
  |
  v
RUNNING
  |
  v
FAILED
```

Cancellation:

```
QUEUED/RUNNING
      |
      v
  CANCELLED
```

Invalid transitions must be rejected.

---

## 23. Frontend Integration

The frontend must provide the complete workflow:

```
Login
  |
Dashboard
  |
New Scan
  |
Scan Progress
  |
Results
  |
Findings
  |
Risk
  |
AI Explanation
  |
Report
```

The frontend must communicate only through the documented API.

It must never access:

- MySQL
- Internal Python modules
- Server filesystem
- Internal network services

---

## 24. Frontend Production Checks

Verify:

- Responsive design
- Accessibility
- Loading states
- Empty states
- Error states
- Network failures
- Authentication expiration
- Safe URL rendering
- XSS-safe rendering
- Safe AI content rendering

Security decisions must remain server-side.

---

## 25. Report Integration

The final report should contain:

- Target
- Scan timestamp
- Scan status
- Risk score
- Risk classification
- Finding summary
- Severity distribution
- Detailed findings
- Evidence
- Remediation guidance
- AI explanation where available

AI-generated explanations must be clearly identified as AI-generated
supporting content.

---

## 26. Production Web Server

Nginx should provide:

- HTTPS termination
- Reverse proxy
- Request limits
- Connection limits
- Security headers
- Static file handling where applicable
- Access logs
- Error logs

Architecture:

```
Client
  |
 HTTPS
  |
Nginx
  |
FastAPI
```

Internal application ports should not be publicly exposed.

---

## 27. Application Process Management

Production processes should be managed reliably.

Recommended:

```
systemd
   |
Gunicorn
   |
Uvicorn Workers
   |
FastAPI
```

Verify:

- Startup
- Restart
- Crash recovery
- Graceful shutdown
- Worker health

---

## 28. Production Security Configuration

Verify:

- HTTPS
- Secure cookies where applicable
- Security headers
- Restricted CORS
- Rate limiting
- Request size limits
- Connection timeouts
- Scan timeouts
- Resource limits
- Safe error responses

Never disable security controls simply to make the deployment easier.

---

## 29. Logging

Production logs should contain useful operational information.

**Log:**

- Startup
- Shutdown
- Authentication events
- Scan creation
- Scan completion
- Scan failure
- Validation rejection
- Security events
- AI failures
- Unexpected exceptions

**Never log:**

- Passwords
- API keys
- Authorization tokens
- Private keys
- Sensitive cookies
- Secrets

---

## 30. Monitoring

Monitor:

- Application health
- Database health
- API errors
- Scan failures
- Scan duration
- Worker health
- CPU
- Memory
- AI provider failures

Health checks should distinguish between:

```
Application Alive
       |
       v
Database Ready
       |
       v
System Ready
```

---

## 31. Performance Verification

Perform final controlled performance tests.

Measure:

- API response time
- Scan duration
- Database query latency
- Concurrent scan behavior
- CPU usage
- Memory usage
- Worker utilization

Verify resource limits remain active.

---

## 32. Concurrent Scan Verification

Run multiple authorized controlled scans.

```
Scan A ----+
Scan B ----+--> Scan Manager
Scan C ----+
```

Verify:

- Correct scan ownership
- Correct scan status
- Correct findings
- Correct risk score
- No cross-user data leakage
- No shared-state corruption
- Controlled resource usage

---

## 33. Final Security Verification

Before release, verify:

**Application Security**
- [ ] Authentication
- [ ] Authorization
- [ ] IDOR protection
- [ ] Input validation
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection where applicable
- [ ] CORS
- [ ] Security headers
- [ ] Rate limiting

**Network Security**
- [ ] SSRF
- [ ] DNS validation
- [ ] Redirect validation
- [ ] TLS verification
- [ ] Timeout limits
- [ ] Port restrictions
- [ ] Egress controls where applicable

**AI Security**
- [ ] Prompt injection protection
- [ ] Sensitive data redaction
- [ ] Output validation
- [ ] AI timeout
- [ ] AI rate/cost limits
- [ ] AI fallback
- [ ] No AI authority over findings/risk

---

## 34. Final Dependency Review

Before deployment:

- Review dependency versions
- Check known vulnerabilities
- Remove unnecessary dependencies
- Run configured security scanners
- Run static analysis
- Run linting
- Run formatting checks
- Run tests

Critical dependency vulnerabilities must be reviewed before release.

---

## 35. Secret Review

Perform a final repository scan.

Verify no credentials exist in:

- Source code
- Configuration
- Documentation
- Test files
- Git history where practical
- Frontend JavaScript

The following must never contain production secrets:

- `frontend/`
- `Docs/`
- `tests/`
- `.env.example`
- Git repository

---

## 36. Demo Environment

Prepare a controlled demonstration environment.

The demo target should intentionally contain documented security
configuration weaknesses.

Example:

```
Demo Target
     |
     v
Security Weaknesses
     |
     v
Auditor
     |
     v
Findings
     |
     v
Risk Score
     |
     v
AI Explanation
```

Only authorized targets may be used.

---

## 37. Recommended Demo Findings

The demo target should ideally demonstrate several categories:

- Missing HSTS
- Missing CSP
- Missing security headers
- Weak cookie configuration
- TLS configuration issue
- Certificate-related issue

The exact findings must correspond to implemented scanner rules.

---

## 38. Hackathon Demo Flow

### Step 1 — Problem

Explain:

> Modern web applications can use HTTPS while still having important TLS and
> HTTP security configuration weaknesses.

### Step 2 — Target

Enter the authorized demonstration URL.

### Step 3 — Scan

Show:

```
Validating target...
Target approved.
Starting scan...
Analyzing TLS...
Analyzing HTTP...
Generating findings...
Calculating risk...
```

### Step 4 — Results

Show:

- Risk score
- Severity distribution
- Findings
- Evidence

### Step 5 — AI Explanation

Open one finding and show:

- What it means
- Why it matters
- Potential impact
- Recommended remediation

### Step 6 — SSRF Protection

Attempt an unsafe controlled target.

Show:

```
Target
  |
Validation
  |
Unsafe
  |
BLOCKED
```

### Step 7 — Conclusion

Explain the product value:

> The platform turns complex web security configuration analysis into
> actionable findings, deterministic risk assessment, and understandable
> remediation guidance.

---

## 39. Demo Failure Strategy

The demo must not depend on one external service.

Prepare fallback behavior for:

- AI provider unavailable
- Demo target unavailable
- TLS failure
- Database delay
- API timeout
- Network interruption

The deterministic scanner must remain demonstrable without AI.

---

## 40. Documentation Verification

Verify all documentation before final submission:

```
Docs/
├── AI_MODEL.md
├── API.md
├── ARCHITECTURE.md
├── DATABASE.md
├── DEMO.md
├── DEPLOYMENT.md
├── ROADMAP.md
├── SCANNER_SPECIFICATION.md
├── SECURITY.md
├── SRS.md
├── TESTING.md
└── UI_UX.md
```

Verify all phase documents:

```
Phases/
├── PHASE_01_FOUNDATION.md
├── PHASE_02_DATABASE.md
├── PHASE_03_TARGET_SECURITY.md
├── PHASE_04_SCANNER.md
├── PHASE_05_FINDING_RISK.md
├── PHASE_06_API_SCAN_MANAGER.md
├── PHASE_07_FRONTEND.md
├── PHASE_08_AI.md
├── PHASE_09_TESTING_HARDENING.md
└── PHASE_10_INTEGRATION_DEPLOYMENT.md
```

Documentation must describe the actual implementation.

---

## 41. Final Repository Review

Verify:

```
git status
git diff
git log
```

Remove:

- Debug files
- Temporary scripts
- Local databases
- Cache files
- Test credentials
- Development secrets
- Unused code
- Unnecessary dependencies

Verify the repository is clean and reproducible.

---

## 42. Final End-to-End Test

The final E2E scenario should be:

```
Login
  |
Dashboard
  |
Submit Target
  |
Validate Target
  |
Start Scan
  |
TLS/HTTP Analysis
  |
Generate Findings
  |
Calculate Risk
  |
Persist Results
  |
Generate AI Explanation
  |
Display Results
  |
Generate Report
```

This workflow must complete successfully using a controlled authorized target.

---

## 43. Release Checklist

**Application**
- [ ] Application starts
- [ ] Health endpoint works
- [ ] Readiness endpoint works
- [ ] Database connection works
- [ ] Migrations work
- [ ] Authentication works
- [ ] Authorization works
- [ ] Scan creation works
- [ ] Scan lifecycle works
- [ ] Scanner works
- [ ] Findings work
- [ ] Risk calculation works
- [ ] AI explanation works
- [ ] AI fallback works
- [ ] Reports work

**Security**
- [ ] SSRF protection verified
- [ ] Redirect protection verified
- [ ] Authentication verified
- [ ] Authorization verified
- [ ] IDOR protection verified
- [ ] SQL injection protection verified
- [ ] XSS protection verified
- [ ] Rate limiting verified
- [ ] CORS verified
- [ ] Security headers verified
- [ ] Secrets removed
- [ ] Logs reviewed

**Infrastructure**
- [ ] HTTPS configured
- [ ] Nginx configured
- [ ] Gunicorn configured
- [ ] systemd configured
- [ ] Database backup configured
- [ ] Monitoring configured
- [ ] Resource limits configured
- [ ] Firewall reviewed

**Testing**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] API tests pass
- [ ] E2E tests pass
- [ ] Security tests pass
- [ ] AI tests pass
- [ ] Database tests pass
- [ ] Regression tests pass
- [ ] Performance tests pass

**Demo**
- [ ] Demo target prepared
- [ ] Demo flow tested
- [ ] Screenshots prepared
- [ ] Backup demo prepared
- [ ] AI fallback verified
- [ ] SSRF demonstration verified
- [ ] Final presentation reviewed

---

## 44. AI Coding Agent Prompt

Use the following prompt when implementing Phase 10:

```
You are a senior software architect, security engineer, QA engineer,
DevOps engineer, and release engineer.

You are working on:

AI-Powered Web Security Configuration Auditor

Implement PHASE 10 — INTEGRATION, DEMO & DEPLOYMENT.

This is the final implementation phase.

==================================================
DOCUMENTS
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
Phases/PHASE_09_TESTING_HARDENING.md

==================================================
PRIMARY OBJECTIVE
==================================================

Integrate the complete existing application and prepare it for final
demonstration and production deployment.

The complete workflow must work:

Authentication
    ->
Target Submission
    ->
Target Validation
    ->
SSRF Protection
    ->
Scan Manager
    ->
TLS/HTTP Scanner
    ->
Finding Engine
    ->
Risk Engine
    ->
Database
    ->
AI Explanation
    ->
API
    ->
Frontend
    ->
Report

==================================================
IMPORTANT
==================================================

Do NOT rewrite working modules unnecessarily.

Do NOT duplicate business logic.

Preserve existing functionality.

Do not introduce major new scanner features.

==================================================
SECURITY RULE
==================================================

This is a defensive security auditing project.

Do NOT add:

- Exploitation
- Brute force
- Credential attacks
- Malware
- Unauthorized scanning
- Payload delivery
- Offensive capabilities

Use only authorized and controlled targets.

==================================================
SSRF RULE
==================================================

Target validation MUST happen before network access.

Do not bypass:

- URL validation
- DNS validation
- IP validation
- Private address protection
- Loopback protection
- Link-local protection
- Metadata protection
- Redirect validation
- Port restrictions

Never disable TLS certificate verification globally.

==================================================
AI RULE
==================================================

AI is explanation-only.

AI MUST NOT:

- Create authoritative findings
- Change severity
- Calculate risk
- Change risk score
- Change scan status
- Bypass SSRF
- Bypass authorization
- Execute remediation

Deterministic security logic remains authoritative.

==================================================
PRODUCTION
==================================================

Verify:

- Environment configuration
- MySQL
- Alembic
- Nginx
- HTTPS
- Gunicorn
- Uvicorn
- systemd
- Logging
- Monitoring
- Rate limiting
- Resource limits
- Secure CORS
- Security headers

Never hardcode production secrets.

==================================================
TESTING
==================================================

Run the complete test suite.

Verify:

- Unit tests
- Integration tests
- API tests
- E2E tests
- Security tests
- SSRF tests
- Authentication tests
- Authorization tests
- Database tests
- AI tests
- Frontend tests
- Regression tests
- Performance tests

Fix failures without weakening security.

==================================================
DEMO
==================================================

Prepare a controlled hackathon demo.

Demonstrate:

1. Target submission
2. Target validation
3. Security scan
4. TLS findings
5. HTTP findings
6. Deterministic risk score
7. AI explanation
8. Report
9. SSRF rejection

The demo must continue working if the AI provider fails.

==================================================
FINAL REPOSITORY REVIEW
==================================================

Before completion:

- Run git status
- Review git diff
- Search for secrets
- Remove debug code
- Remove temporary files
- Verify .gitignore
- Verify documentation
- Verify migrations
- Verify production configuration

==================================================
FINAL REPORT
==================================================

Provide:

1. Files changed
2. Features integrated
3. Tests executed
4. Test results
5. Security checks completed
6. Deployment configuration
7. Demo readiness
8. Known limitations
9. Remaining risks
10. Final release readiness

Do not claim completion if critical tests or security controls are failing.
```

---

## 45. Acceptance Criteria

Phase 10 is complete only when:

- [ ] All application modules are integrated.
- [ ] Complete scan workflow works.
- [ ] Target validation happens before scanning.
- [ ] SSRF protection remains enforced.
- [ ] TLS scanning works.
- [ ] HTTP scanning works.
- [ ] Findings are deterministic.
- [ ] Risk scoring is deterministic.
- [ ] Results persist correctly.
- [ ] Authentication works.
- [ ] Authorization works.
- [ ] Frontend communicates correctly with APIs.
- [ ] AI explanation works.
- [ ] AI failure does not break scanning.
- [ ] Reports work.
- [ ] Production configuration is verified.
- [ ] Database migrations are reproducible.
- [ ] Backup strategy is documented.
- [ ] Monitoring is configured.
- [ ] Security controls are verified.
- [ ] Controlled demo works.
- [ ] Documentation matches implementation.
- [ ] No critical unresolved security issue remains.

---

## 46. Definition of Done

Phase 10 is considered DONE when:

- The application works end-to-end.
- Critical tests pass.
- Critical security controls are verified.
- SSRF protection is verified.
- Authentication and authorization are verified.
- Finding generation is deterministic.
- Risk calculation is deterministic.
- AI remains explanation-only.
- AI failure does not break scanning.
- Database migrations are reproducible.
- Production configuration is validated.
- Logging and monitoring are available.
- Controlled demo works reliably.
- Documentation is synchronized.
- Repository is ready for final submission.

---

## 47. Phase Completion Record

After successful implementation:

```
Phase: 10
Status: COMPLETED
Implementation Date: YYYY-MM-DD

Integration:
- End-to-End Flow: PASS
- API Integration: PASS
- Frontend Integration: PASS
- Database Integration: PASS
- AI Integration: PASS

Security:
- SSRF: PASS
- Authentication: PASS
- Authorization: PASS
- IDOR: PASS
- Input Validation: PASS
- AI Security: PASS
- Secrets Review: PASS

Testing:
- Total:
- Passed:
- Failed:
- Skipped:

Deployment:
- HTTPS: PASS
- Nginx: PASS
- Gunicorn: PASS
- Database: PASS
- Monitoring: PASS
- Backup: PASS

Demo:
- Status: READY

Known Limitations:
- ...

Final Release:
- READY / NOT READY
```

---

## 48. Final Project Principle

The final product must follow:

```
Secure Input
     |
Secure Validation
     |
Secure Scan
     |
Deterministic Findings
     |
Deterministic Risk
     |
AI Explanation
     |
Actionable Report
```

The security engine is authoritative.

The AI layer is supportive.

The final principle is:

> AI explains what the security engine discovered.
> AI does not decide what the security engine discovered.