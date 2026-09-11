# AI-Powered Web Security Configuration Auditor

## API Specification

**Version:** 1.0
**API Style:** REST
**Backend:** FastAPI
**Database:** MySQL 8.x
**Frontend:** HTML5, CSS3, Vanilla JavaScript
**Status:** Initial / Development Baseline

---

## 1. Purpose

This document defines the REST API contract for the AI-Powered Web Security Configuration Auditor.

The API provides controlled access to:

- Authentication
- User management
- Scan creation
- Scan status
- Scan results
- Security findings
- Risk scores
- Reports
- Dashboard statistics
- Health monitoring

The API must follow the security requirements defined in:

```
SRS.md
ARCHITECTURE.md
DATABASE.md
SCANNER_SPECIFICATION.md
SECURITY.md
```

---

## 2. API Architecture

```
                  FRONTEND
              HTML/CSS/JS
                    |
                    | HTTPS
                    v
                FASTAPI
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
      Auth       Scan API    Report API
                    |
                    v
              Scan Manager
                    |
                    v
             Scanner Worker
                    |
                    v
                  MySQL
```

---

## 3. Base URL

Development:

```
http://localhost:8000/api
```

Production:

```
https://<domain>/api
```

The production API must use HTTPS.

---

## 4. API Versioning

The initial API version is: `/api/v1`

Example:

```
GET /api/v1/health
```

Future breaking changes should introduce a new API version.

---

## 5. Content Type

JSON is the default API format.

Request: `Content-Type: application/json`

Response: `Content-Type: application/json`

---

## 6. Standard Response Format

Successful responses should use a predictable structure.

Example:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully"
}
```

---

## 7. Standard Error Format

Errors should use:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Production errors must not expose:

- Stack traces
- Database errors
- Internal paths
- Secrets
- Environment variables
- Internal service details

---

## 8. HTTP Status Codes

The API should use standard HTTP status codes.

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 202 | Request accepted for background processing |
| 204 | Successful request with no response body |
| 400 | Invalid request |
| 401 | Authentication required |
| 403 | Access denied |
| 404 | Resource not found |
| 409 | Resource conflict |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | External target/service error |
| 503 | Service unavailable |

---

## 9. Authentication

Protected endpoints require authentication.

Possible implementation: HTTP-only secure session cookie, or Bearer token.

The exact implementation should be finalized during backend development.

Authentication secrets must never be exposed to frontend JavaScript unnecessarily.

---

## 10. Authorization

Authentication alone is insufficient.

Every protected resource must verify ownership or permission.

Example:

```
User A
  |
  v
GET /scans/123
  |
  v
Ownership Check
  |
  +---- Allowed
  |
  +---- Denied
```

Changing a scan ID must never expose another user's scan.

---

## 11. Health Endpoint

```
GET /api/v1/health
```

**Purpose:** Check whether the API is running.

Response:

```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

---

## 12. Readiness Endpoint

```
GET /api/v1/health/ready
```

**Purpose:** Check whether required services are available.

Possible checks:

- API
- Database
- Scanner Worker
- AI Service

Example response:

```json
{
  "success": true,
  "data": {
    "status": "ready",
    "database": "healthy",
    "scanner": "healthy",
    "ai": "available"
  }
}
```

If AI is unavailable, deterministic scanning should still remain functional.

---

## 13. Authentication Endpoints

## 14. Register

```
POST /api/v1/auth/register
```

**Purpose:** Create a user account.

Request:

```json
{
  "name": "Demo User",
  "email": "user@example.com",
  "password": "secure-password"
}
```

Validation:

- `name`: required, maximum length enforced
- `email`: required, valid email format
- `password`: required, minimum strength requirements

Response:

```json
{
  "success": true,
  "message": "Account created successfully"
}
```

Passwords must never be returned.

---

## 15. Login

```
POST /api/v1/auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

Successful response:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid",
      "name": "Demo User",
      "email": "user@example.com"
    }
  }
}
```

Authentication session/token must be handled securely.

---

## 16. Logout

```
POST /api/v1/auth/logout
```

**Purpose:** Terminate the current authenticated session.

Response:

```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

## 17. Current User

```
GET /api/v1/auth/me
```

**Purpose:** Return the currently authenticated user.

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Demo User",
    "email": "user@example.com"
  }
}
```

---

## 18. Create Scan

```
POST /api/v1/scans
```

**Purpose:** Create a new security scan.

**Authentication:** Required

Request:

```json
{
  "target_url": "https://example.com"
}
```

---

## 19. Scan URL Validation

The backend must validate:

- Scheme
- Hostname
- Port
- DNS
- Resolved IP
- SSRF policy

before creating a scan job.

Allowed:

```
http://example.com
https://example.com
```

Rejected:

```
file://...
localhost
127.0.0.1
10.x.x.x
192.168.x.x
169.254.169.254
```

See `SECURITY.md` for the complete SSRF policy.

---

## 20. Create Scan Response

The recommended response is `HTTP 202 Accepted`.

Example:

```json
{
  "success": true,
  "message": "Scan started",
  "data": {
    "scan_id": "uuid",
    "status": "queued"
  }
}
```

---

## 21. Scan Status

```
GET /api/v1/scans/{scan_id}
```

**Purpose:** Retrieve scan status.

Response:

```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "target_url": "https://example.com",
    "status": "running",
    "progress": 45,
    "created_at": "2026-09-11T10:00:00Z",
    "started_at": "2026-09-11T10:00:02Z",
    "completed_at": null
  }
}
```

---

## 22. Scan Status Values

Allowed statuses:

- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`

State transition:

```
QUEUED
   |
   v
RUNNING
   |
 +----+----+
 |         |
 v         v
COMPLETED FAILED
```

Optional future state: `CANCELLED`

---

## 23. Scan Progress

Progress should represent scanner execution.

Example:

```
0%
 |
 v
Target Validation
 |
20%
 |
 v
TLS Scanner
 |
40%
 |
 v
Header Scanner
 |
60%
 |
 v
Cookie Scanner
 |
75%
 |
 v
Content Scanner
 |
90%
 |
 v
Risk Engine
 |
100%
 |
 v
Completed
```

Progress must never exceed `0 - 100`.

---

## 24. Scan List

```
GET /api/v1/scans
```

**Purpose:** Return scans belonging to the authenticated user.

Query parameters: `page`, `limit`, `status`, `sort`

Example:

```
GET /api/v1/scans?page=1&limit=20&status=completed
```

Response:

```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 42
    }
  }
}
```

---

## 25. Pagination

Default: `page = 1`, `limit = 20`

Maximum: `limit = 100`

The API must reject unreasonable values.

---

## 26. Scan Results

```
GET /api/v1/scans/{scan_id}/results
```

**Purpose:** Return complete structured scan results.

Response:

```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "target_url": "https://example.com",
    "status": "completed",
    "summary": {},
    "tls": {},
    "headers": {},
    "cookies": [],
    "redirects": [],
    "mixed_content": [],
    "resources": [],
    "findings": [],
    "risk": {}
  }
}
```

---

## 27. TLS Result

Example:

```json
{
  "certificate": {
    "valid": true,
    "issuer": "Example CA",
    "expires_at": "2027-01-01T00:00:00Z",
    "days_remaining": 112,
    "hostname_match": true,
    "self_signed": false
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

## 28. Header Result

Example:

```json
{
  "name": "Strict-Transport-Security",
  "present": false,
  "value": null,
  "status": "missing"
}
```

---

## 29. Cookie Result

Example:

```json
{
  "name": "session_id",
  "secure": true,
  "http_only": true,
  "same_site": "Lax"
}
```

Sensitive cookie values must never be returned or stored unnecessarily.

---

## 30. Redirect Result

Example:

```json
{
  "source": "http://example.com",
  "status_code": 301,
  "destination": "https://example.com",
  "is_https": true
}
```

---

## 31. Finding Result

Every finding should follow a common schema.

```json
{
  "id": "uuid",
  "code": "HEADER_HSTS_MISSING",
  "category": "security_headers",
  "title": "Strict-Transport-Security header is missing",
  "severity": "HIGH",
  "confidence": 1.0,
  "evidence": {
    "header": "Strict-Transport-Security",
    "observed": false
  },
  "impact": "The browser does not receive an HSTS policy from the tested response.",
  "recommendation": "Configure an appropriate HSTS policy after confirming HTTPS is correctly deployed."
}
```

---

## 32. Severity Values

Allowed: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`

---

## 33. Confidence

Confidence is represented as a value between `0.0` and `1.0`.

Example:

```json
{
  "confidence": 0.97
}
```

---

## 34. Risk Summary

Example:

```json
{
  "score": 72,
  "level": "HIGH",
  "critical": 0,
  "high": 3,
  "medium": 4,
  "low": 2,
  "info": 5
}
```

---

## 35. Risk Levels

Initial levels:

| Range | Level |
|---|---|
| 0 - 19 | LOW |
| 20 - 39 | MODERATE |
| 40 - 59 | MEDIUM |
| 60 - 79 | HIGH |
| 80 - 100 | CRITICAL |

The exact scoring formula is defined by the Risk Engine.

---

## 36. Report Endpoint

```
GET /api/v1/scans/{scan_id}/report
```

**Purpose:** Return a human-readable security report.

Response:

```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "target": "https://example.com",
    "executive_summary": "...",
    "risk": {},
    "findings": [],
    "recommendations": []
  }
}
```

---

## 37. AI Explanation Endpoint

```
GET /api/v1/scans/{scan_id}/ai-summary
```

**Purpose:** Return an AI-generated explanation of deterministic scan results.

Response:

```json
{
  "success": true,
  "data": {
    "summary": "...",
    "key_risks": [],
    "recommendations": []
  }
}
```

The AI must only receive structured evidence required for explanation.

---

## 38. AI Failure

If AI processing fails:

```json
{
  "success": false,
  "error": {
    "code": "AI_UNAVAILABLE",
    "message": "AI explanation is currently unavailable."
  }
}
```

The underlying security scan remains valid.

---

## 39. Dashboard Statistics

```
GET /api/v1/dashboard
```

**Purpose:** Return user dashboard information.

Example:

```json
{
  "success": true,
  "data": {
    "total_scans": 25,
    "completed_scans": 23,
    "running_scans": 1,
    "failed_scans": 1,
    "average_score": 61,
    "critical_findings": 2,
    "high_findings": 8,
    "medium_findings": 14,
    "low_findings": 9
  }
}
```

---

## 40. Finding Filtering

The results API may support: `severity`, `category`, `status`

Example:

```
GET /api/v1/scans/{scan_id}/findings?severity=HIGH
```

---

## 41. Findings Endpoint

```
GET /api/v1/scans/{scan_id}/findings
```

Response:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "TLS_1_0_ENABLED",
        "severity": "HIGH",
        "confidence": 1.0
      }
    ]
  }
}
```

---

## 42. Scan Cancellation

```
POST /api/v1/scans/{scan_id}/cancel
```

**Purpose:** Cancel a running scan.

Only scans owned by the authenticated user may be cancelled.

Response:

```json
{
  "success": true,
  "message": "Scan cancellation requested"
}
```

The scanner must stop safely without corrupting database state.

---

## 43. Delete Scan

```
DELETE /api/v1/scans/{scan_id}
```

**Purpose:** Delete a user's scan and associated data.

**Authorization:** Owner only

Response: `204 No Content`

Deletion behavior must follow the data-retention policy.

---

## 44. API Rate Limiting

Rate limiting should be applied to:

```
POST /auth/login
POST /auth/register
POST /scans
POST /scans/{id}/cancel
```

The API should return `429 Too Many Requests` when limits are exceeded.

---

## 45. API Request Limits

The backend should enforce maximum lengths.

Example:

- `target_url`: maximum reasonable URL length
- `name`: maximum configured length
- `email`: maximum configured length

Limits must be enforced server-side.

---

## 46. URL Validation Error

Example:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_TARGET_URL",
    "message": "The target URL is invalid or unsupported."
  }
}
```

Do not reveal internal SSRF validation details unnecessarily.

---

## 47. SSRF Block Error

Example:

```json
{
  "success": false,
  "error": {
    "code": "TARGET_NOT_ALLOWED",
    "message": "The target is not allowed for security scanning."
  }
}
```

The frontend should display a safe human-readable message.

---

## 48. Validation Error

FastAPI/Pydantic validation errors should be normalized into the application's standard error format.

Example:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more input fields are invalid."
  }
}
```

---

## 49. Not Found Error

Example:

```json
{
  "success": false,
  "error": {
    "code": "SCAN_NOT_FOUND",
    "message": "The requested scan was not found."
  }
}
```

The API should avoid revealing whether another user's resource exists.

---

## 50. Unauthorized Access

If authentication is missing: `401 Unauthorized`

Example:

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication is required."
  }
}
```

---

## 51. Forbidden Access

If the user is authenticated but lacks permission: `403 Forbidden`

Example:

```json
{
  "success": false,
  "error": {
    "code": "ACCESS_DENIED",
    "message": "You do not have permission to access this resource."
  }
}
```

---

## 52. API Request ID

Each request should have a unique request identifier.

Example: `X-Request-ID: uuid`

This identifier should be included in logs.

---

## 53. Scan ID

Every scan should have a unique identifier.

Recommended: UUID

Example: `550e8400-e29b-41d4-a716-446655440000`

The scan ID must not expose sensitive information.

---

## 54. API Idempotency

Future versions may support an idempotency key for scan creation.

Example: `Idempotency-Key: unique-client-generated-value`

This prevents accidental duplicate scans.

---

## 55. API Security Headers

The API should return appropriate security headers.

At minimum:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

Production HTTPS deployments should also use HSTS.

---

## 56. CORS

Only explicitly configured frontend origins should be allowed.

Example: `https://auditor.example.com`

Wildcard CORS should not be used for authenticated production APIs.

---

## 57. Database Interaction

API routes must not directly construct unsafe SQL queries.

Recommended architecture:

```
API Route
   |
   v
Service Layer
   |
   v
Repository / ORM
   |
   v
MySQL
```

SQLAlchemy should be used for database interaction.

---

## 58. API Layer Separation

Recommended backend structure:

```
app/
|
+-- api/
|   +-- routes/
|       +-- auth.py
|       +-- scans.py
|       +-- findings.py
|       +-- dashboard.py
|       +-- health.py
|
+-- services/
|   +-- scan_service.py
|   +-- risk_service.py
|   +-- ai_service.py
|
+-- scanners/
|
+-- models/
|
+-- schemas/
|
+-- repositories/
|
+-- core/
```

---

## 59. Pydantic Schemas

Request and response models should use Pydantic.

Example:

```python
class ScanCreateRequest(BaseModel):
    target_url: HttpUrl
```

Additional custom validation must enforce the application's SSRF and target policy.

---

## 60. Background Processing

Scan creation should not keep an HTTP connection open for the entire scan.

Recommended:

```
POST /scans
      |
      v
Create Scan
      |
      v
202 Accepted
      |
      v
Background Worker
      |
      v
Scanner
```

Frontend polls or receives future real-time updates.

---

## 61. Scan Polling

Frontend may poll `GET /api/v1/scans/{scan_id}` until `completed` or `failed`.

Recommended polling interval: `2 - 5 seconds`

The exact value may be adjusted.

---

## 62. API Timeout

Normal API requests should have reasonable server-side timeouts.

Long-running scanner execution must be handled asynchronously.

---

## 63. API Logging

Log:

- timestamp
- request_id
- endpoint
- HTTP method
- status code
- duration
- user identifier where appropriate
- scan_id where applicable

Never log:

- passwords
- tokens
- API keys
- session cookies
- database passwords

---

## 64. API Testing

The API must be tested at multiple levels.

**Unit Tests** — Test:
- Pydantic validation
- URL validation
- Risk calculations
- Authorization logic

**Integration Tests** — Test:
- API + MySQL
- API + Scanner
- API + Authentication

**Security Tests** — Test:
- SQL injection
- XSS
- IDOR
- SSRF
- Rate limiting
- Authentication bypass
- Invalid input

---

## 65. Example Complete Scan Flow

```
1. User logs in
        |
        v
2. Frontend sends POST /scans
        |
        v
3. FastAPI validates request
        |
        v
4. SSRF validation
        |
        v
5. Scan record created
        |
        v
6. HTTP 202 returned
        |
        v
7. Background worker starts
        |
        v
8. TLS Scanner
        |
        v
9. Header Scanner
        |
        v
10. Cookie Scanner
        |
        v
11. Redirect Scanner
        |
        v
12. Content Scanner
        |
        v
13. Finding Engine
        |
        v
14. Risk Engine
        |
        v
15. AI Explanation
        |
        v
16. MySQL stores results
        |
        v
17. Frontend requests results
        |
        v
18. Security Report displayed
```

---

## 66. API Contract Principle

The API must separate:

```
Transport
    |
    v
Validation
    |
    v
Business Logic
    |
    v
Scanner
    |
    v
Risk Engine
    |
    v
Persistence
```

Routes must remain thin.

Business logic should not be placed directly inside route handlers.

---

## 67. API Design Principles

The API follows:

- RESTful resource design
- Explicit validation
- Secure authentication
- Ownership-based authorization
- Consistent error responses
- Rate limiting
- SSRF protection
- Asynchronous scan execution
- Deterministic security results
- Safe AI integration
- Structured logging
- Versioned endpoints

---

## 68. MVP Endpoint Summary

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/health` | Health check | No |
| GET | `/api/v1/health/ready` | Readiness check | No |
| POST | `/api/v1/auth/register` | Register | No |
| POST | `/api/v1/auth/login` | Login | No |
| POST | `/api/v1/auth/logout` | Logout | Yes |
| GET | `/api/v1/auth/me` | Current user | Yes |
| POST | `/api/v1/scans` | Create scan | Yes |
| GET | `/api/v1/scans` | List scans | Yes |
| GET | `/api/v1/scans/{id}` | Scan status | Yes |
| GET | `/api/v1/scans/{id}/results` | Scan results | Yes |
| GET | `/api/v1/scans/{id}/findings` | Findings | Yes |
| GET | `/api/v1/scans/{id}/report` | Security report | Yes |
| GET | `/api/v1/scans/{id}/ai-summary` | AI summary | Yes |
| POST | `/api/v1/scans/{id}/cancel` | Cancel scan | Yes |
| DELETE | `/api/v1/scans/{id}` | Delete scan | Yes |
| GET | `/api/v1/dashboard` | Dashboard | Yes |

---

## 69. Future API Features

Potential future endpoints:

```
POST /api/v1/scans/bulk
GET  /api/v1/reports/{id}/pdf
GET  /api/v1/scans/{id}/export
GET  /api/v1/organizations
POST /api/v1/teams
GET  /api/v1/schedules
POST /api/v1/schedules
GET  /api/v1/webhooks
```

These are not part of the MVP unless required.

---

## 70. Final API Architecture

```
                     FRONTEND
                  Vanilla JS
                       |
                       v
                 REST API /v1
                       |
          +------------+------------+
          |            |            |
          v            v            v
        AUTH         SCANS       REPORTS
                       |
                       v
                 SCAN SERVICE
                       |
                       v
                SECURITY POLICY
                       |
                       v
                  SCANNER ENGINE
                       |
          +------------+------------+
          |            |            |
          v            v            v
         TLS         HTTP        CONTENT
          |            |            |
          +------------+------------+
                       |
                       v
                 FINDING ENGINE
                       |
                       v
                   RISK ENGINE
                       |
                  +----+----+
                  |         |
                  v         v
                MySQL       AI
                  |         |
                  +----+----+
                       |
                       v
                    REPORT
```

---

## 71. Final API Rule

> The API controls access. The scanner performs observation. The finding engine determines security issues. The risk engine determines priority. AI explains the results.