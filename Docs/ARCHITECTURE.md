# AI-Powered Web Security Configuration Auditor

## System Architecture Document

**Version:** 1.0
**Project Type:** Hackathon Project
**Domain:** Cybersecurity & Data Protection
**Problem Statement:** Problem 4.3 — Hidden SSL/TLS and Web Security Configuration Weaknesses
**Architecture Status:** Initial / Development Baseline

---

## 1. Architecture Overview

The AI-Powered Web Security Configuration Auditor is a defensive web-security assessment platform designed to identify publicly observable SSL/TLS and web-security configuration weaknesses.

The system follows a modular architecture in which deterministic security scanners collect technical evidence, a finding engine converts evidence into structured findings, a risk engine prioritizes the findings, and an AI layer converts technical results into understandable explanations and remediation guidance.

The core architecture follows this principle:

```
TARGET
   |
   v
COLLECT
   |
   v
ANALYZE
   |
   v
FINDINGS
   |
   v
RISK SCORING
   |
   +----------------+
   |                |
   v                v
DATABASE           AI
   |                |
   +-------+--------+
           |
           v
      SECURITY REPORT
```

---

## 2. Architectural Goals

The architecture is designed around the following goals:

1. Modular security scanners.
2. Deterministic security checks.
3. Clear separation between scanning and AI.
4. Secure handling of user-supplied URLs.
5. Controlled resource consumption.
6. Reproducible security scoring.
7. Easy addition of new scanners.
8. Simple deployment.
9. Maintainable codebase.
10. Hackathon-friendly implementation speed.

---

## 3. High-Level System Architecture

The system consists of the following major components:

- Frontend
- API Layer
- Scan Orchestrator
- Security Scanner Engine
- Finding Engine
- Risk Engine
- AI Service
- Database Layer
- Report Service

### 3.1 High-Level Diagram

```
                         +----------------------+
                         |        USER          |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |   HTML / CSS / JS    |
                         |      Frontend        |
                         +----------+-----------+
                                    |
                              REST API / JSON
                                    |
                                    v
                         +----------------------+
                         |       FastAPI        |
                         |      API Layer       |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |  Scan Orchestrator   |
                         +----------+-----------+
                                    |
                 +------------------+------------------+
                 |                  |                  |
                 v                  v                  v
        +----------------+ +----------------+ +----------------+
        | TLS Scanner    | | HTTP Scanner   | | Content Scanner|
        +----------------+ +----------------+ +----------------+
                 |                  |                  |
                 +------------------+------------------+
                                    |
                                    v
                         +----------------------+
                         |   Finding Engine     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     Risk Engine      |
                         +----------+-----------+
                                    |
                    +---------------+---------------+
                    |                               |
                    v                               v
             +--------------+                +-------------+
             |    MySQL     |                | AI Service  |
             |   Database   |                |             |
             +--------------+                +-------------+
                    |                               |
                    +---------------+---------------+
                                    |
                                    v
                         +----------------------+
                         |   Report Generator   |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |    Security Report   |
                         |     / Dashboard      |
                         +----------------------+
```

---

## 4. Frontend Architecture

The frontend will use:

- HTML5
- CSS3
- Vanilla JavaScript (ES6+)

No frontend framework will be used for the MVP.

The frontend will communicate with the FastAPI backend through REST APIs.

### 4.1 Frontend Responsibilities

The frontend is responsible for:

- Website URL input
- Scan initiation
- Scan progress display
- Security score visualization
- Finding display
- Severity indicators
- Category summaries
- Finding details
- AI explanations
- Remediation recommendations
- Scan history
- Report visualization

### 4.2 Frontend Structure

```
frontend/
|
+-- index.html
+-- scan.html
+-- report.html
|
+-- css/
|   +-- style.css
|   +-- dashboard.css
|   +-- report.css
|   +-- responsive.css
|
+-- js/
|   +-- api.js
|   +-- scanner.js
|   +-- dashboard.js
|   +-- report.js
|   +-- components.js
|
+-- assets/
    +-- icons/
    +-- images/
```

---

## 5. Backend Architecture

The backend will use:

- Python
- FastAPI
- Uvicorn
- SQLAlchemy

The backend follows a modular service-oriented structure.

### 5.1 Backend Responsibilities

The backend will:

- Validate scan requests.
- Manage scan lifecycle.
- Execute security scanners.
- Collect technical evidence.
- Generate findings.
- Calculate risk scores.
- Store scan results.
- Request AI explanations.
- Generate reports.
- Return results to the frontend.

---

## 6. Backend Component Architecture

```
backend/
|
+-- app/
    |
    +-- main.py
    |
    +-- config.py
    |
    +-- api/
    |   |
    |   +-- routes/
    |       +-- scans.py
    |       +-- reports.py
    |       +-- auth.py
    |
    +-- scanners/
    |   +-- base_scanner.py
    |   +-- tls_scanner.py
    |   +-- header_scanner.py
    |   +-- cookie_scanner.py
    |   +-- redirect_scanner.py
    |   +-- content_scanner.py
    |   +-- resource_scanner.py
    |
    +-- services/
    |   +-- scan_service.py
    |   +-- risk_engine.py
    |   +-- finding_service.py
    |   +-- ai_service.py
    |   +-- report_service.py
    |
    +-- models/
    |   +-- user.py
    |   +-- scan.py
    |   +-- finding.py
    |   +-- certificate.py
    |   +-- security_header.py
    |   +-- cookie.py
    |   +-- redirect.py
    |   +-- resource.py
    |   +-- ai_report.py
    |
    +-- schemas/
    |   +-- scan.py
    |   +-- finding.py
    |   +-- report.py
    |
    +-- database/
    |   +-- connection.py
    |   +-- session.py
    |
    +-- utils/
        +-- url_validator.py
        +-- network.py
        +-- logging.py
```

---

## 7. API Layer

FastAPI will provide the REST API used by the frontend.

The API layer is responsible for:

- Request validation
- Authentication where applicable
- Authorization
- Response formatting
- Error handling
- Rate limiting
- Calling application services

### 7.1 Main API Endpoints

```
POST   /api/scans
GET    /api/scans/{scan_id}
GET    /api/scans/{scan_id}/findings
GET    /api/scans/{scan_id}/report
GET    /api/scans/history
```

---

## 8. Scan Orchestrator

The Scan Orchestrator is responsible for managing the complete scanning workflow.

It coordinates individual scanners without placing scanner-specific logic inside the API layer.

### 8.1 Scan Flow

```
Scan Request
     |
     v
URL Validation
     |
     v
Create Scan Record
     |
     v
Start Scan
     |
     +-----------------------------+
     |                             |
     v                             v
TLS Scanner                 HTTP Scanner
     |                             |
     v                             v
Certificate                 Headers
Protocol                    Cookies
Configuration               Redirects
     |                             |
     +-------------+---------------+
                   |
                   v
            Content Scanner
                   |
                   v
            Resource Analysis
                   |
                   v
            Finding Engine
                   |
                   v
              Risk Engine
                   |
                   +----------+
                   |          |
                   v          v
                MySQL       AI Service
                   |          |
                   +-----+----+
                         |
                         v
                  Final Report
```

---

## 9. Scanner Engine

The Scanner Engine is the core technical component of the application.

Each scanner should perform one well-defined category of security analysis.

### 9.1 Scanner Design Principle

Every scanner should follow:

```
Input
  |
  v
Collection
  |
  v
Analysis
  |
  v
Evidence
  |
  v
Structured Result
```

Scanners must not directly:

- Calculate the overall security score.
- Generate AI explanations.
- Modify unrelated scanner results.
- Perform exploitation.

---

## 10. TLS Scanner

**File:** `app/scanners/tls_scanner.py`

Responsibilities:

- Establish TLS connection.
- Inspect certificate.
- Validate hostname.
- Inspect certificate dates.
- Identify issuer.
- Inspect SAN entries.
- Detect self-signed certificates.
- Analyze supported TLS protocol versions where technically possible.

### 10.1 TLS Output

Example:

```json
{
  "hostname": "example.com",
  "certificate": {
    "valid": true,
    "hostname_match": true,
    "self_signed": false,
    "issuer": "Example CA",
    "days_remaining": 120
  },
  "protocols": {
    "tls_1_0": false,
    "tls_1_1": false,
    "tls_1_2": true,
    "tls_1_3": true
  }
}
```

---

## 11. HTTP Scanner

**File:** `app/scanners/header_scanner.py`

Responsibilities:

- Fetch HTTP/HTTPS responses.
- Inspect response headers.
- Identify security headers.
- Analyze basic header configuration.

### 11.1 Headers

Initial headers:

- Strict-Transport-Security
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy

---

## 12. Cookie Scanner

**File:** `app/scanners/cookie_scanner.py`

Responsibilities:

- Inspect Set-Cookie headers.
- Identify security attributes.
- Analyze cookie configuration.

Attributes:

- Secure
- HttpOnly
- SameSite
- Domain
- Path
- Expires
- Max-Age

---

## 13. Redirect Scanner

**File:** `app/scanners/redirect_scanner.py`

Responsibilities:

- Analyze HTTP-to-HTTPS redirects.
- Record redirect status codes.
- Record redirect chain.
- Detect excessive redirects.
- Detect redirect loops.
- Identify final destination.

### 13.1 Redirect Example

```
http://example.com
        |
        | 301
        v
https://example.com
```

---

## 14. Content Scanner

**File:** `app/scanners/content_scanner.py`

Responsibilities:

- Analyze HTML responses.
- Identify embedded resources.
- Detect HTTP resources loaded by HTTPS pages.
- Detect mixed content.

Potential resource types:

- `<script>`
- `<img>`
- `<link>`
- `<iframe>`
- `<video>`
- `<audio>`
- `<object>`

---

## 15. Resource Analyzer

**File:** `app/scanners/resource_scanner.py`

Responsibilities:

- Identify resource URLs.
- Determine same-origin vs third-party resources.
- Identify external domains.
- Categorize resources where possible.

Example:

```
example.com
|
+-- Same Origin
|
+-- cdn.example.com
|
+-- analytics.example.com
|
+-- external-service.com
```

Third-party resources must not automatically be classified as vulnerabilities.

---

## 16. Finding Engine

The Finding Engine converts raw scanner results into standardized security findings.

### 16.1 Finding Pipeline

```
Scanner Result
      |
      v
Rule Evaluation
      |
      v
Finding Created
      |
      v
Evidence Attached
      |
      v
Severity Assigned
      |
      v
Confidence Assigned
```

### 16.2 Finding Structure

```json
{
  "category": "security_headers",
  "title": "Missing HSTS",
  "severity": "HIGH",
  "confidence": 1.0,
  "evidence": {
    "header": "Strict-Transport-Security",
    "observed": false
  }
}
```

---

## 17. Risk Engine

The Risk Engine converts findings into an overall security posture score.

Responsibilities:

- Severity evaluation
- Category weighting
- Confidence consideration
- Priority calculation
- Overall score calculation
- Risk-level classification

### 17.1 Risk Levels

| Score Range | Risk Level |
|---|---|
| 90 - 100 | Excellent |
| 75 - 89 | Good |
| 60 - 74 | Moderate |
| 40 - 59 | Weak |
| 0 - 39 | Critical |

These thresholds may be adjusted after testing.

---

## 18. Risk Calculation Principle

The scoring engine must be deterministic.

The same scanner results should produce the same score.

AI must not directly determine the numerical security score.

### 18.1 Initial Category Weights

| Category | Weight |
|---|---|
| TLS / SSL | 25% |
| Security Headers | 25% |
| Cookies | 15% |
| Redirects | 15% |
| Content Security | 15% |
| Other Configuration | 5% |

The exact scoring formula will be documented in the Scanner Specification and may be tuned during development.

---

## 19. AI Architecture

The AI Service is an assistive component.

AI does not perform the primary security scan.

### 19.1 AI Flow

```
Security Scanner
       |
       v
Structured Finding
       |
       v
Risk Engine
       |
       v
AI Service
       |
       v
Explanation
       |
       v
Remediation
```

### 19.2 AI Input

The AI should receive structured security findings rather than uncontrolled raw target content.

Example:

```json
{
  "category": "transport_security",
  "finding": "missing_hsts",
  "severity": "HIGH",
  "evidence": "Strict-Transport-Security header was not observed"
}
```

### 19.3 AI Output

The AI should produce:

- What was found
- Why it matters
- Potential security impact
- Recommended remediation

AI output should remain tied to scanner evidence.

---

## 20. AI Hallucination Protection

The system must ensure that AI cannot create unsupported security claims.

The architecture follows:

```
Observed Evidence
       |
       v
Deterministic Rule
       |
       v
Finding
       |
       v
AI Explanation
```

The AI is not allowed to introduce new technical findings that were not detected by the scanner.

---

## 21. Database Architecture

The application will use:

- MySQL 8.x

SQLAlchemy will provide database interaction.

### 21.1 Database Relationship

```
User
 |
 +---- Scan
        |
        +---- Finding
        |
        +---- Certificate
        |
        +---- Security Header
        |
        +---- Cookie
        |
        +---- Redirect
        |
        +---- Resource
        |
        +---- AI Report
```

---

## 22. Core Database Entities

Initial entities:

- users
- scans
- findings
- certificates
- security_headers
- cookies
- redirects
- resources
- ai_reports

Detailed database design will be maintained in: `docs/DATABASE.md`

---

## 23. Scan State Architecture

A scan progresses through defined states.

```
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

Possible failure:

```
Any Stage
   |
   v
FAILED
```

Individual scanner failures should not necessarily fail the complete scan.

---

## 24. Partial Failure Architecture

Example:

```
TLS Scanner       SUCCESS
Header Scanner    SUCCESS
Cookie Scanner    SUCCESS
Redirect Scanner  SUCCESS
Content Scanner   FAILED
```

The scan may still complete.

The final report should indicate that content analysis was unavailable.

Example:

```
Content analysis could not be completed.

Reason:
Target response exceeded the configured analysis limit.
```

---

## 25. Security Architecture

Security is a core architectural requirement.

The application shall implement:

- URL validation
- SSRF protection
- Request timeouts
- Redirect limits
- Response-size limits
- Rate limiting
- Concurrent scan limits
- Input validation
- Secure secret management
- Parameterized database access
- Safe logging

---

## 26. SSRF Protection

Because the application accepts user-provided URLs, SSRF is considered a critical architectural risk.

The scanner must not blindly request arbitrary internal addresses.

The URL validation layer should consider:

- Loopback addresses
- Private IP ranges
- Link-local addresses
- Localhost
- Internal hostnames
- Unsafe redirect destinations
- Cloud metadata endpoints

The scanner must revalidate destinations after redirects.

---

## 27. Network Safety

Every outgoing scan request should have limits.

Initial controls:

- Connection timeout
- Read timeout
- Maximum redirects
- Maximum response size
- Maximum resources analyzed
- Maximum concurrent scans

The scanner should use a controlled HTTP client configuration.

---

## 28. Frontend-to-Backend Data Flow

```
User enters URL
       |
       v
JavaScript validates input
       |
       v
POST /api/scans
       |
       v
FastAPI
       |
       v
Scan Service
       |
       v
Scanner Engine
       |
       v
Database
       |
       v
API Response
       |
       v
JavaScript
       |
       v
Dashboard
```

---

## 29. Report Generation

The Report Service combines:

- Scan metadata
- Security score
- Risk level
- Findings
- Evidence
- AI explanations
- Recommendations

into a single security report.

### 29.1 Report Structure

```
Security Report
|
+-- Target Information
|
+-- Security Score
|
+-- Risk Level
|
+-- Executive Summary
|
+-- TLS / SSL
|
+-- Security Headers
|
+-- Cookies
|
+-- Redirects
|
+-- Content Security
|
+-- Third-Party Resources
|
+-- Findings
|
+-- Recommendations
|
+-- Assessment Limitations
```

---

## 30. Deployment Architecture

The production deployment will use Linux and Nginx.

### 30.1 Deployment Diagram

```
                    INTERNET
                       |
                       v
                  +---------+
                  |  Nginx  |
                  +----+----+
                       |
             +---------+---------+
             |                   |
             v                   v
       Static Frontend       FastAPI
                                 |
                                 v
                           Scan Engine
                                 |
                  +--------------+--------------+
                  |                             |
                  v                             v
               MySQL                       AI Service
```

Nginx will act as:

- Reverse proxy
- HTTPS termination layer
- Static file server
- Request filtering layer
- Rate-limiting layer where configured

---

## 31. Development Architecture

During development:

```
Frontend
localhost:5500
     |
     | REST API
     v
FastAPI
localhost:8000
     |
     v
MySQL
localhost:3306
```

---

## 32. Production Architecture

Production:

```
HTTPS
  |
  v
Nginx
  |
  +---------> Frontend Static Files
  |
  +---------> FastAPI
                   |
                   +----> MySQL
                   |
                   +----> AI Provider
```

---

## 33. Error Handling Architecture

Errors should be handled at the appropriate layer.

```
Frontend Error
      |
      v
API Error Handler
      |
      v
Service Error
      |
      v
Scanner Error
```

Errors should return structured API responses.

Example:

```json
{
  "success": false,
  "error": {
    "code": "TARGET_UNREACHABLE",
    "message": "The target could not be reached."
  }
}
```

---

## 34. Logging Architecture

The application will maintain structured logs for:

- Scan creation
- Scan completion
- Scanner execution
- Scanner failures
- API errors
- Database errors
- AI service errors
- Performance metrics

Sensitive values such as:

- Passwords
- API keys
- Tokens
- Secrets

must never be written to logs.

---

## 35. Extensibility Architecture

New scanners should be addable without modifying the entire system.

Example future architecture:

```
Scanner Engine
|
+-- TLS Scanner
+-- Header Scanner
+-- Cookie Scanner
+-- Redirect Scanner
+-- Content Scanner
+-- Resource Scanner
|
+-- Future:
    +-- DNS Scanner
    +-- CORS Scanner
    +-- Cache Scanner
    +-- CSP Analyzer
    +-- Certificate Transparency Analyzer
```

---

## 36. Scanner Interface

Scanners should follow a common conceptual interface.

```python
class BaseScanner:

    async def scan(self, target):
        """
        Perform a security assessment and return
        structured scanner results.
        """
        raise NotImplementedError
```

A scanner should return structured data rather than directly writing to the database.

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

## 37. Separation of Responsibilities

The system follows strict responsibility separation.

```
API Layer
    |
    |-- Request / Response

Scan Service
    |
    |-- Workflow Management

Scanner
    |
    |-- Technical Security Analysis

Finding Engine
    |
    |-- Finding Creation

Risk Engine
    |
    |-- Severity / Score / Priority

AI Service
    |
    |-- Explanation / Remediation

Database Layer
    |
    |-- Persistence

Report Service
    |
    |-- Result Presentation
```

---

## 38. Security Boundaries

The architecture contains the following security boundaries:

```
                USER INPUT
                    |
                    v
              URL VALIDATOR
                    |
                    v
              NETWORK LAYER
                    |
                    v
             SCANNER ENGINE
                    |
                    v
            FINDING / RISK ENGINE
                    |
          +---------+---------+
          |                   |
          v                   v
       DATABASE             AI API
```

Untrusted target content must never be treated as trusted application instructions.

---

## 39. Performance Architecture

The initial architecture prioritizes reliable sequential scanning.

Where appropriate, independent scanners may execute concurrently.

Example:

```
                 Scan
                  |
        +---------+---------+
        |         |         |
        v         v         v
       TLS     Headers   Redirects
        |         |         |
        +---------+---------+
                  |
                  v
             Content
                  |
                  v
              Scoring
```

Concurrency must remain bounded to prevent excessive resource usage.

---

## 40. Hackathon MVP Architecture

The first implementation will focus on:

1. FastAPI
2. URL validation
3. TLS Scanner
4. Header Scanner
5. Cookie Scanner
6. Redirect Scanner
7. Content Scanner
8. Finding Engine
9. Risk Engine
10. MySQL persistence
11. AI explanation
12. HTML/CSS/JS dashboard

Authentication, advanced monitoring, notifications, PDF generation, and enterprise functionality are secondary.

---

## 41. Controlled Demonstration Architecture

The hackathon demonstration will use a controlled website environment.

The demo environment will contain intentionally configured weaknesses such as:

- Missing HSTS
- Missing security headers
- Weak cookie configuration
- Mixed content
- Redirect configuration issue

The system will scan the controlled environment.

Expected demonstration:

```
Initial Configuration
        |
        v
Security Scan
        |
        v
38 / 100
CRITICAL
        |
        v
Fix Configuration
        |
        v
Scan Again
        |
        v
94 / 100
GOOD
```

This demonstrates:

```
Detection
   +
Evidence
   +
Risk Assessment
   +
Remediation
   +
Verification
```

---

## 42. Architectural Principles

The following principles must be followed throughout development:

**Principle 1 — Evidence First**
Every security finding should have supporting technical evidence.

**Principle 2 — Deterministic Security**
Security checks and scoring must be deterministic.

**Principle 3 — AI as an Assistant**
AI explains findings; it does not replace the scanner.

**Principle 4 — Defensive by Design**
The platform must avoid exploitation and destructive testing.

**Principle 5 — Least Privilege**
Components should receive only the permissions they require.

**Principle 6 — Fail Safely**
Scanner failures should produce controlled errors rather than unsafe behavior.

**Principle 7 — Modular Design**
Every scanner should remain independently testable.

**Principle 8 — Explainability**
Every finding should be understandable to both technical and non-technical users.

**Principle 9 — Reproducibility**
The same target and configuration should produce consistent results within the same scanning conditions.

**Principle 10 — Security Over Features**
A smaller secure implementation is preferred over a larger insecure implementation.

---

## 43. Architecture Decision Summary

| Decision | Choice | Reason |
|---|---|---|
| Frontend | HTML/CSS/Vanilla JS | Lightweight and fast to develop |
| Backend | FastAPI | High-performance Python API framework |
| Database | MySQL 8.x | Reliable relational database and team familiarity |
| ORM | SQLAlchemy | Maintainable database abstraction |
| TLS | Python ssl/socket/cryptography | Direct TLS and certificate analysis |
| HTTP | httpx | Modern HTTP client with timeout support |
| HTML | BeautifulSoup4 | HTML/resource analysis |
| AI | LLM API | Human-readable explanations and remediation |
| Reverse Proxy | Nginx | Production proxy and static serving |
| Testing | Pytest | Backend and scanner testing |
| Containers | Docker | Optional deployment consistency |

---

## 44. Final Architecture

The complete system can be summarized as:

```
                         WEB SECURITY AUDITOR
                                  |
                                  v
                         +----------------+
                         |   Frontend     |
                         | HTML/CSS/JS    |
                         +-------+--------+
                                 |
                              REST API
                                 |
                                 v
                         +----------------+
                         |    FastAPI     |
                         +-------+--------+
                                 |
                         Scan Orchestrator
                                 |
              +------------------+------------------+
              |                  |                  |
              v                  v                  v
         TLS Scanner       HTTP Scanner       Content Scanner
              |                  |                  |
              +------------------+------------------+
                                 |
                                 v
                         Finding Engine
                                 |
                                 v
                           Risk Engine
                            /       \
                           /         \
                          v           v
                       MySQL         AI
                          \           /
                           \         /
                            v       v
                         Report Service
                               |
                               v
                         Security Dashboard
```

The architecture is intentionally designed to remain simple enough for hackathon implementation while providing a strong foundation for future production-scale security monitoring.