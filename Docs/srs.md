# Software Requirements Specification (SRS)

# AI-Powered Web Security Configuration Auditor

| **Field** | **Details** |
|---|---|
| **Version** | 1.0 |
| **Project Type** | Hackathon Project |
| **Domain** | Cybersecurity & Data Protection |
| **Problem Statement** | Problem 4.3 — Hidden SSL/TLS and Web Security Configuration Weaknesses |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python + FastAPI |
| **Database** | MySQL 8.x |
| **Document Status** | Initial / Development Baseline |

---

# 1. Introduction

## 1.1 Purpose

The **AI-Powered Web Security Configuration Auditor** is a defensive cybersecurity platform designed to help small organizations, independent website owners, and non-security professionals identify hidden SSL/TLS and web-security configuration weaknesses in publicly accessible websites.

A website may appear completely functional in a browser while still having security weaknesses such as:

* Expired or misconfigured TLS certificates
* Insecure or deprecated TLS protocol configurations
* Missing or weak HTTP security headers
* Insecure cookie attributes
* Improper HTTP-to-HTTPS redirects
* Mixed content
* Potentially risky third-party resources
* Other publicly observable web-security configuration issues

The system will automatically analyze these configurations, assign severity and risk scores, explain findings in understandable language, and provide prioritized remediation guidance.

The system is intended to make web-security assessment more accessible without requiring users to understand complex security terminology.

---

## 1.2 Problem Statement

Small organizations and independent website owners frequently rely on default hosting configurations, plugins, copied deployment configurations, or third-party infrastructure.

A website may function normally while still lacking important security protections.

Common hidden weaknesses include:

* Expired certificates
* Incomplete certificate chains
* Hostname mismatches
* Weak or deprecated TLS configurations
* Missing security headers
* Contradictory security headers
* Missing cookie security attributes
* Improper redirect behavior
* Mixed-content resources
* Risky or unexpected third-party resources

These weaknesses are difficult for non-specialists to identify because browsers generally do not expose the complete security posture of a website.

The proposed system addresses this gap by providing an automated, understandable, and evidence-based security configuration assessment.

---

## 1.3 Objectives

The primary objectives are:

1. Analyze publicly observable SSL/TLS configuration.
2. Validate TLS certificate properties.
3. Identify deprecated or insecure TLS configurations.
4. Analyze HTTP security headers.
5. Analyze security-related cookie attributes.
6. Analyze HTTP-to-HTTPS redirect behavior.
7. Detect mixed-content resources.
8. Identify and categorize third-party resources.
9. Generate structured security findings.
10. Calculate an overall security posture score.
11. Prioritize findings according to severity and potential impact.
12. Provide understandable explanations of security issues.
13. Provide actionable remediation guidance.
14. Maintain scan history for authenticated users.
15. Provide a professional security dashboard.
16. Ensure scans are performed defensively without exploitation.
17. Clearly communicate assessment limitations and confidence.

---

# 2. Scope

## 2.1 In Scope

The first version of the system will support:

### SSL/TLS Assessment

* Certificate validity
* Certificate expiration
* Certificate issuer
* Certificate subject
* Subject Alternative Names (SAN)
* Hostname verification
* Self-signed certificate detection
* Certificate chain analysis where observable
* TLS protocol support analysis
* TLS 1.0 detection
* TLS 1.1 detection
* TLS 1.2 detection
* TLS 1.3 detection
* Basic TLS configuration assessment

### HTTP Security Assessment

* HTTPS availability
* HTTP-to-HTTPS redirect behavior
* Redirect chain analysis
* HTTP response headers
* Security header presence
* Security header configuration assessment

### Security Headers

The system should initially evaluate:

* Strict-Transport-Security
* Content-Security-Policy
* X-Content-Type-Options
* X-Frame-Options
* Referrer-Policy
* Permissions-Policy

Additional headers may be added in future versions.

### Cookie Security

The system will inspect publicly observable `Set-Cookie` response attributes including:

* Secure
* HttpOnly
* SameSite
* Cookie name
* Cookie scope where observable

The system should avoid declaring a cookie insecure solely because an attribute is absent when the context does not justify such a conclusion.

### Content Analysis

The system will analyze publicly accessible HTML for:

* HTTP resources embedded in HTTPS pages
* Scripts
* Images
* Stylesheets
* Iframes
* Other relevant externally loaded resources

### Third-Party Resources

The system may identify externally hosted resources and categorize them as:

* Same-origin
* Third-party
* CDN
* Analytics
* External service
* Unknown third-party resource

Third-party presence alone must not automatically be treated as a vulnerability.

### Risk Assessment

The system will:

* Categorize findings
* Assign severity
* Calculate confidence
* Calculate risk priority
* Generate an overall security score
* Group findings by category

### AI Assistance

AI will be used for:

* Plain-language explanations
* Security impact explanations
* Remediation guidance
* Finding summarization
* Executive-level summaries

AI must not replace deterministic security checks.

---

## 2.2 Out of Scope

The following capabilities are explicitly outside the initial scope:

* Exploiting discovered vulnerabilities
* SQL injection exploitation
* XSS exploitation
* Credential attacks
* Password cracking
* Brute-force attacks
* Denial-of-service testing
* Malware scanning
* Unauthorized penetration testing
* Authentication bypass
* Privilege escalation
* Automated exploitation
* Destructive security testing
* Accessing private resources
* Circumventing access controls

The platform is intended as a **defensive configuration auditor**, not an offensive penetration-testing framework.

---

# 3. Target Users

## 3.1 Small Business Website Owners

Users who operate websites but do not have dedicated cybersecurity teams.

## 3.2 Developers

Developers who want to verify security configuration before or after deployment.

## 3.3 DevOps / System Administrators

Users responsible for web servers, HTTPS configuration, certificates, and deployment infrastructure.

## 3.4 Security Professionals

Security teams can use the system as a lightweight external configuration assessment tool.

## 3.5 Students and Learners

Students can use the platform to understand real-world web-security configuration issues.

---

# 4. Product Overview

The system will follow this workflow:

```text
User
  |
  v
Enter Website URL
  |
  v
Validate Target
  |
  v
Start Security Scan
  |
  v
Scan Orchestrator
  |
  +--------------------+
  |                    |
  v                    v
TLS Scanner       HTTP Scanner
  |                    |
  +---------+----------+
            |
            v
     Content Analyzer
            |
            v
     Cookie Analyzer
            |
            v
      Finding Engine
            |
            v
       Risk Engine
            |
      +-----+------+
      |            |
      v            v
    MySQL        AI Layer
      |            |
      +-----+------+
            |
            v
     Security Report
```

---

# 5. Functional Requirements

## FR-01 — User Registration and Authentication

The system may provide user authentication for storing scan history.

The system should support:

* User registration
* Login
* Logout
* Password hashing
* Session/token management
* User-specific scan history

Authentication should not be required for a basic demonstration scan if the hackathon MVP prioritizes rapid access.

---

## FR-02 — Website URL Submission

The user shall be able to submit a website URL.

Example:

```text
https://example.com
```

The system shall:

1. Validate URL syntax.
2. Validate supported protocols.
3. Normalize the target URL.
4. Prevent unsupported or malformed targets.
5. Start a security scan after validation.

---

## FR-03 — Target Validation

The system shall validate:

* URL format
* HTTP/HTTPS protocol
* Hostname
* DNS resolution where required
* Network accessibility
* Redirect destination safety

The system shall reject clearly invalid targets.

The scanner must not attempt to bypass authentication or access controls.

---

# 6. TLS/SSL Requirements

## FR-04 — Certificate Inspection

The system shall inspect the target's TLS certificate.

The system should identify:

* Certificate validity
* Expiration date
* Issuer
* Subject
* SAN entries
* Hostname match
* Self-signed status
* Certificate chain information where available

Example finding:

```text
Certificate expires in 6 days.
Severity: HIGH
```

---

## FR-05 — TLS Protocol Analysis

The system shall assess supported TLS protocol versions where technically possible.

The system should identify:

* TLS 1.0
* TLS 1.1
* TLS 1.2
* TLS 1.3

Deprecated protocols shall be reported as security findings.

The scanner must not attempt aggressive probing or exploitation.

---

## FR-06 — TLS Risk Classification

TLS findings shall be classified according to severity.

Example:

```text
TLS 1.0 enabled
Category: Transport Security
Severity: High
Confidence: High
```

---

# 7. HTTP Security Requirements

## FR-07 — HTTPS Availability

The system shall determine whether HTTPS is available.

The system shall identify whether the target successfully establishes a secure HTTPS connection.

---

## FR-08 — HTTP-to-HTTPS Redirect Analysis

The system shall analyze redirect behavior.

The system should determine:

* Whether HTTP redirects to HTTPS
* Redirect status codes
* Number of redirects
* Redirect chain
* Final destination
* Potential redirect inconsistencies

Example:

```text
HTTP
 |
301
 |
HTTPS
```

---

# 8. Security Header Requirements

## FR-09 — Security Header Detection

The system shall inspect HTTP response headers.

The initial security header set includes:

```text
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
X-Frame-Options
Referrer-Policy
Permissions-Policy
```

---

## FR-10 — Header Configuration Analysis

The system shall evaluate not only header presence but also basic configuration quality.

Example:

```text
Header:
Strict-Transport-Security

Status:
Missing

Severity:
High

Recommendation:
Configure an appropriate HSTS policy after
confirming HTTPS is correctly deployed.
```

---

# 9. Cookie Security Requirements

## FR-11 — Cookie Detection

The system shall inspect publicly observable `Set-Cookie` headers.

The system shall identify:

* Cookie name
* Secure attribute
* HttpOnly attribute
* SameSite attribute
* Domain where observable
* Path where observable
* Expiration information where observable

---

## FR-12 — Cookie Risk Analysis

The system shall identify potentially insecure cookie configurations.

Example:

```text
Session Cookie
Secure: No
HttpOnly: No
SameSite: Missing
```

The system should assign severity based on cookie context and available evidence.

---

# 10. Content Security Requirements

## FR-13 — Mixed Content Detection

The system shall inspect HTTPS pages for resources loaded through HTTP.

The system shall identify resources such as:

* Scripts
* Images
* Stylesheets
* Iframes
* Media
* Other HTTP-linked resources

Example:

```text
HTTPS Page
    |
    +--- HTTP Script
    +--- HTTP Image
    +--- HTTP Iframe
```

The system shall generate a mixed-content finding when appropriate.

---

# 11. Third-Party Resource Requirements

## FR-14 — Third-Party Resource Detection

The system shall identify externally hosted resources.

The system should distinguish:

```text
Same Origin
Third Party
CDN
Analytics
External Service
Unknown
```

The system shall not automatically classify every third-party resource as malicious or vulnerable.

---

# 12. Finding Engine

## FR-15 — Finding Generation

Each identified issue shall produce a structured finding.

A finding should contain:

```text
Finding ID
Scan ID
Category
Title
Description
Evidence
Severity
Confidence
Impact
Recommendation
Detected At
```

Example:

```json
{
  "category": "security_headers",
  "title": "Missing HSTS",
  "severity": "HIGH",
  "confidence": 1.0
}
```

---

# 13. Risk Engine

## FR-16 — Severity Classification

The system shall support:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
PASS
```

Severity must be based on predefined rules rather than AI-generated guesses.

---

## FR-17 — Risk Score

The system shall calculate an overall security score between:

```text
0 - 100
```

Example interpretation:

```text
90-100  Excellent
75-89   Good
60-74   Moderate
40-59   Weak
0-39    Critical
```

These ranges may be adjusted during implementation and testing.

---

## FR-18 — Finding Prioritization

The system shall prioritize findings using factors such as:

* Severity
* Security impact
* Confidence
* Exposure
* Configuration context

The dashboard shall show users which findings should be fixed first.

---

# 14. AI Requirements

## FR-19 — AI Explanation

The AI layer shall convert structured technical findings into understandable explanations.

Example input:

```json
{
  "finding": "Missing HSTS",
  "severity": "HIGH",
  "evidence": "Strict-Transport-Security header absent"
}
```

Example output:

```text
What we found:
HSTS is not configured.

Why it matters:
The browser is not instructed to enforce HTTPS
for future connections.

Recommended action:
Configure an appropriate HSTS policy after
confirming HTTPS is correctly deployed.
```

---

## FR-20 — AI Safety

The AI layer shall not invent technical evidence.

AI explanations must be based only on scanner-generated findings.

The system should preserve the distinction between:

```text
Observed Evidence
        |
        v
Deterministic Finding
        |
        v
AI Explanation
```

The AI shall not independently declare a vulnerability without supporting scanner evidence.

---

# 15. Dashboard Requirements

## FR-21 — Scan Dashboard

The dashboard shall display:

* Target URL
* Scan status
* Security score
* Risk level
* Total findings
* Critical findings
* High findings
* Medium findings
* Low findings
* Passed checks

Example:

```text
SECURITY SCORE

      72 / 100

     MODERATE RISK

Critical     1
High         3
Medium       4
Low          2
Passed      11
```

---

## FR-22 — Security Categories

The dashboard should group results into:

```text
TLS / SSL
Security Headers
Cookies
Redirects
Content Security
Third-Party Resources
```

---

## FR-23 — Finding Details

Users shall be able to open individual findings.

Each finding should display:

```text
Title
Severity
Category
Evidence
Why it matters
Technical explanation
Recommended fix
Confidence
```

---

# 16. Scan History

## FR-24 — Scan Storage

Authenticated users shall be able to view previous scans.

The system should store:

* Target URL
* Scan date
* Security score
* Risk level
* Finding count
* Scan status

---

## FR-25 — Historical Comparison

Future versions may support comparison between scans.

Example:

```text
Previous Score: 38
Current Score: 94

Improvement: +56
```

This feature is particularly useful for demonstrating remediation effectiveness.

---

# 17. Database Requirements

## 17.1 Database

The system shall use:

**MySQL 8.x**

## 17.2 Core Tables

Initial schema should include:

```text
users
scans
findings
certificates
security_headers
cookies
redirects
resources
ai_reports
```

Relationships:

```text
User
 |
 +---- Scan
        |
        +---- Findings
        +---- Certificate
        +---- Headers
        +---- Cookies
        +---- Redirects
        +---- Resources
        +---- AI Report
```

---

# 18. Non-Functional Requirements

## NFR-01 — Performance

For normal publicly accessible websites, the system should provide initial scan results within a reasonable time.

The target MVP should aim for:

```text
Typical scan: < 30 seconds
```

Actual timing may vary based on:

* Target response time
* Network latency
* Redirects
* TLS negotiation
* Number of resources

---

## NFR-02 — Reliability

A failed individual scanner should not necessarily terminate the entire scan.

Example:

```text
TLS Scanner      PASS
Header Scanner   PASS
Cookie Scanner   PASS
Content Scanner  FAILED
```

The system should still return partial results with an appropriate warning.

---

## NFR-03 — Security

The application shall:

* Validate all user input
* Avoid command injection
* Protect database credentials
* Store secrets in environment variables
* Use parameterized queries/ORM
* Avoid logging sensitive information unnecessarily
* Implement request timeouts
* Limit scan resources
* Prevent SSRF where applicable
* Restrict scanning to appropriate publicly accessible targets
* Avoid unauthorized exploitation

---

## NFR-04 — Privacy

The system shall minimize collected information.

The platform should primarily store:

* Target URL
* Scan metadata
* Security findings
* Technical evidence
* Generated reports

The system shall not collect unnecessary personal information.

---

## NFR-05 — Maintainability

The backend shall use modular components.

Scanners must be independently testable.

Example:

```text
TLSScanner
HeaderScanner
CookieScanner
RedirectScanner
ContentScanner
RiskEngine
AIService
```

---

## NFR-06 — Scalability

The architecture should allow additional scanners to be added without significantly modifying existing scanner modules.

Future scanners may include:

* DNS security
* CORS configuration
* Cache security
* Additional security headers
* Certificate transparency awareness
* More advanced web-security configuration analysis

---

# 19. System Architecture

```text
                         USER
                           |
                           v
                +---------------------+
                | HTML/CSS/JS Client  |
                +----------+----------+
                           |
                         REST
                           |
                           v
                +---------------------+
                |       FastAPI       |
                +----------+----------+
                           |
                    Scan Orchestrator
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   TLS Scanner       HTTP Scanner      Content Scanner
        |                  |                  |
        +------------------+------------------+
                           |
                    Finding Engine
                           |
                           v
                     Risk Engine
                     /         \
                    /           \
                   v             v
              MySQL DB       AI Service
                   \             /
                    \           /
                     v         v
                    Security Report
                           |
                           v
                     Web Dashboard
```

---

# 20. Technology Stack

## Frontend

* HTML5
* CSS3
* Vanilla JavaScript (ES6+)

No frontend framework will be used in the MVP.

## Backend

* Python
* FastAPI
* Uvicorn

## Security Analysis

* Python `ssl`
* Python `socket`
* `cryptography`
* `httpx`
* BeautifulSoup4

## Database

* MySQL 8.x
* SQLAlchemy

## AI

* LLM API

## Testing

* Pytest
* Pytest-Asyncio

## Deployment

* Linux
* Nginx
* Uvicorn/Gunicorn-compatible deployment configuration where appropriate
* Docker (optional)

---

# 21. API Requirements

## POST /api/scans

Starts a new scan.

### Request

```json
{
  "url": "https://example.com"
}
```

### Response

```json
{
  "scan_id": "SCAN-12345",
  "status": "queued"
}
```

---

## GET /api/scans/{scan_id}

Returns scan status and results.

Example:

```json
{
  "scan_id": "SCAN-12345",
  "status": "completed",
  "security_score": 72,
  "risk_level": "MODERATE"
}
```

---

## GET /api/scans/{scan_id}/findings

Returns findings for a scan.

---

## GET /api/scans/{scan_id}/report

Returns the complete security report.

---

# 22. Scan Lifecycle

```text
CREATED
   |
   v
VALIDATING
   |
   v
QUEUED
   |
   v
SCANNING
   |
   v
ANALYZING
   |
   v
SCORING
   |
   v
AI_PROCESSING
   |
   v
COMPLETED
```

Failure state:

```text
SCANNING
   |
   v
FAILED
```

Partial failures should be represented separately from complete scan failure.

---

# 23. Security Score Model

The initial scoring model may use weighted categories.

Example:

```text
TLS / SSL              25%
Security Headers       25%
Cookies                15%
Redirects              15%
Content Security       15%
Other Configuration     5%
```

The final scoring algorithm shall be documented separately in the technical design document.

The score must be deterministic and reproducible.

---

# 24. Severity Model

## Critical

Severe configuration weakness with potentially significant security implications.

## High

Important security weakness requiring prompt remediation.

## Medium

Security weakness that should be addressed as part of normal hardening.

## Low

Minor weakness or hardening opportunity.

## Informational

Useful security information that does not necessarily represent a vulnerability.

## Pass

Security control appears correctly configured based on the performed assessment.

---

# 25. Error Handling

The system shall gracefully handle:

* Invalid URL
* DNS failure
* Connection timeout
* TLS handshake failure
* Certificate errors
* HTTP errors
* Redirect loops
* Unsupported content
* Rate limiting
* Target unavailable
* Scanner-specific failures
* AI service failure
* Database failure

Example:

```text
Target could not be scanned.

Reason:
Connection timed out.

No security conclusion was generated
for unavailable checks.
```

---

# 26. Logging

The backend should log:

* Scan lifecycle
* Scanner execution
* Errors
* Performance metrics
* API errors

Logs should not unnecessarily contain:

* Passwords
* Authentication tokens
* API keys
* Sensitive user information

---

# 27. Rate Limiting and Resource Protection

The scanner shall implement reasonable controls such as:

* Request timeout
* Maximum redirect count
* Maximum response size
* Maximum number of analyzed resources
* API rate limiting
* Concurrent scan limits

These controls prevent the platform from becoming an accidental denial-of-service tool.

---

# 28. Ethical and Legal Requirements

The platform is designed for defensive security assessment.

Users should scan only:

* Websites they own
* Websites they are authorized to assess
* Public targets where scanning is permitted

The system shall not provide automated exploitation functionality.

The product interface should communicate this clearly.

Example:

```text
Use this scanner only on websites you own
or are authorized to assess.
```

---

# 29. Limitations

The platform performs an external configuration assessment.

It cannot guarantee complete website security.

A successful scan does not mean:

```text
"No vulnerabilities exist."
```

Instead, the correct interpretation is:

```text
"No issues were detected within the
scope of the implemented checks."
```

The system cannot reliably determine:

* Server-side vulnerabilities not externally observable
* Application logic flaws
* Authentication vulnerabilities
* Internal network weaknesses
* Vulnerabilities behind authentication
* Zero-day vulnerabilities
* Complete organizational security posture

---

# 30. Future Enhancements

Potential future capabilities:

1. Continuous website monitoring
2. Scheduled security scans
3. Security score history
4. Scan comparison
5. Email alerts
6. Slack/Teams notifications
7. PDF reports
8. DNS security analysis
9. CORS analysis
10. CSP visualizer
11. Certificate expiry alerts
12. Multi-domain monitoring
13. Organization/team accounts
14. Role-based access control
15. Security compliance mapping
16. CI/CD integration
17. GitHub/GitLab integration
18. Cloud deployment
19. Security posture APIs
20. Enterprise dashboards

---

# 31. MVP Definition

The hackathon MVP shall prioritize the following:

```text
1. URL submission
2. TLS certificate analysis
3. TLS protocol analysis
4. Security header analysis
5. Cookie analysis
6. HTTP/HTTPS redirect analysis
7. Mixed-content detection
8. Finding generation
9. Risk scoring
10. Professional dashboard
11. AI explanation
12. Scan report
```

The following features are secondary:

```text
- Authentication
- Scan history
- Third-party categorization
- Historical comparison
- PDF export
- Notifications
```

The team shall prioritize a fully working core scanner over a large number of incomplete features.

---

# 32. Hackathon Demonstration Flow

The recommended demonstration shall use a controlled environment.

## Step 1 — Introduce the Problem

Explain:

> A website can look perfectly normal to a user while silently having multiple security configuration weaknesses.

## Step 2 — Enter Target

```text
https://demo-target.example
```

## Step 3 — Run Scan

Show:

```text
Scanning TLS...
Analyzing headers...
Checking cookies...
Analyzing redirects...
Inspecting resources...
Calculating risk...
```

## Step 4 — Display Security Score

Example:

```text
38 / 100
CRITICAL
```

## Step 5 — Show Findings

```text
CRITICAL    1
HIGH        3
MEDIUM      4
LOW         2
PASSED      8
```

## Step 6 — Open Finding

Show:

```text
Missing HSTS

Evidence:
Strict-Transport-Security header not observed.

Why it matters:
The browser is not instructed to enforce
HTTPS for future connections.

Recommended action:
Configure an appropriate HSTS policy after
verifying HTTPS deployment.
```

## Step 7 — Demonstrate Remediation

Fix the controlled demo configuration.

Run the scan again.

Example:

```text
38 / 100
   ↓
94 / 100
```

## Step 8 — Final Message

> We don't just tell website owners that their website has security weaknesses. We identify the evidence, prioritize the risks, explain them in understandable language, and show how remediation improves the security posture.

---

# 33. Success Criteria

The project will be considered successful if it can:

* Accept a valid website URL.
* Perform a complete external security configuration assessment.
* Detect representative TLS weaknesses.
* Detect representative security-header weaknesses.
* Detect representative cookie weaknesses.
* Detect redirect issues.
* Detect mixed-content issues.
* Generate deterministic findings.
* Produce a reproducible security score.
* Explain findings clearly.
* Provide actionable remediation guidance.
* Display results in a professional dashboard.
* Demonstrate measurable improvement after controlled remediation.

---

# 34. Requirements Traceability

| Problem Statement Requirement       | System Feature                |
| ----------------------------------- | ----------------------------- |
| Expired certificates                | Certificate Analyzer          |
| Incomplete certificate chains       | TLS Certificate Analyzer      |
| Wrong hostnames                     | Hostname/SAN Validation       |
| Insecure protocol settings          | TLS Protocol Analyzer         |
| Missing security headers            | Header Scanner                |
| Contradictory/weak headers          | Header Configuration Analyzer |
| Insecure cookies                    | Cookie Analyzer               |
| Redirect behavior                   | Redirect Scanner              |
| Embedded third-party content        | Resource Analyzer             |
| Hidden weaknesses                   | Automated Security Assessment |
| Difficult for non-specialists       | AI Explanation Layer          |
| Risk prioritization                 | Risk Engine                   |
| Avoidable privacy/security exposure | Security Recommendations      |

---

# 35. Conclusion

The AI-Powered Web Security Configuration Auditor provides an accessible defensive solution for discovering hidden web-security configuration weaknesses.

The platform combines deterministic security analysis with risk scoring and AI-assisted explanations.

The central design principle is:

```text
DETECT
   ↓
EVIDENCE
   ↓
CLASSIFY
   ↓
PRIORITIZE
   ↓
EXPLAIN
   ↓
REMEDIATE
   ↓
VERIFY
```

The system is designed to transform complex web-security configuration information into clear, actionable security intelligence for small organizations and non-specialist website owners.
