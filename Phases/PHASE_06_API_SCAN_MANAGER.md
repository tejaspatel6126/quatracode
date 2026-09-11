# PHASE 06 — SCAN MANAGEMENT & API

## 1. Phase Overview

**Phase:** 06  
**Name:** Scan Management & API  
**Status:** Planned  
**Depends On:** Phase 05 — Finding & Risk Engine  
**Next Phase:** Phase 07 — Frontend & Dashboard

---

## 2. Objective

The objective of Phase 06 is to connect the security scanning pipeline
to the application's backend API and database.

This phase introduces the complete scan lifecycle:

```text
API Request
    |
    v
Authentication
    |
    v
Target Validation
    |
    v
Scan Creation
    |
    v
Scanner
    |
    v
Findings + Risk
    |
    v
Database
    |
    v
API Response
```

The API must provide a secure and predictable interface for creating,
monitoring, retrieving, and managing security scans.

---

## 3. Core Principle

The API is an orchestration layer.

It must NOT independently implement:

- SSRF protection
- TLS detection
- Security header detection
- Finding rules
- Risk calculations

Those responsibilities already belong to earlier phases.

```
Phase 03
Target Security
      |
      v
Phase 04
Scanner
      |
      v
Phase 05
Finding + Risk
      |
      v
Phase 06
API + Scan Management
```

---

## 4. Documents To Follow

Implementation must follow:

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
Phases/
├── PHASE_01_FOUNDATION.md
├── PHASE_02_DATABASE.md
├── PHASE_03_TARGET_SECURITY.md
├── PHASE_04_SCANNER.md
├── PHASE_05_FINDING_RISK.md
└── PHASE_06_API_SCAN_MANAGER.md
```

---

## 5. Scope

### Included

Phase 06 includes:

- Scan API
- Scan creation
- Scan lifecycle
- Scan status
- Scan execution
- Scan persistence
- Scan result retrieval
- Finding retrieval
- Risk result retrieval
- Scan history
- Authentication integration
- Authorization
- API validation
- Pagination
- Error handling
- Request IDs
- Rate limiting integration
- Scan cancellation where supported
- API security tests
- Integration tests

### Not Included

Do NOT implement:

- Dashboard UI
- Advanced frontend interactions
- AI explanations
- Report generation
- Email notifications
- Scheduled scans
- Advanced background job infrastructure
- Production deployment

These belong to later phases.

---

## 6. Scan Lifecycle

A scan must have a well-defined lifecycle.

Recommended states:

```
QUEUED
  |
  v
RUNNING
  |
  +----> COMPLETED
  |
  +----> FAILED
  |
  +----> CANCELLED
```

Invalid state transitions must be rejected.

---

## 7. Scan State Machine

```
        +---------+
        | QUEUED  |
        +----+----+
             |
             v
        +---------+
        | RUNNING |
        +----+----+
          /   |   \
         v    v    v
 COMPLETED  FAILED CANCELLED
```

A completed scan must not transition back to running.

A failed scan must not silently become completed.

---

## 8. Scan Creation

The API should provide a scan creation endpoint according to:

```
Docs/API.md
```

Conceptually:

```
POST /api/v1/scans
```

Request:

```json
{
  "target_url": "https://example.com"
}
```

The exact request schema must follow Docs/API.md.

---

## 9. Scan Creation Flow

```
POST /scans
     |
     v
Authenticate User
     |
     v
Validate Request
     |
     v
Validate Target
     |
     v
Create Scan
     |
     v
Execute Scan
     |
     v
Persist Results
```

The API must never skip target validation.

---

## 10. Authentication

Scan APIs must require authenticated users where defined by the project
security model.

Unauthenticated access to protected scan endpoints must be rejected.

Example:

```
Unauthenticated Request
        |
        v
       401
```

Authentication implementation must follow the existing project
architecture.

Do not introduce a second authentication system unnecessarily.

---

## 11. Authorization

Authentication alone is not sufficient.

A user must only access scans they are authorized to access.

Example:

```
User A
  |
  +--> Scan A -> ALLOW
  |
  +--> Scan B owned by User B -> BLOCK
```

Unauthorized scan access must return the appropriate API error.

---

## 12. Object-Level Authorization

Every scan-related operation must verify ownership or permission.

This includes:

- get scan
- get scan status
- get findings
- get risk
- delete scan if supported
- cancel scan if supported
- retrieve scan history

Never rely only on the scan ID.

---

## 13. Scan Identifier

Scans must use a stable unique identifier.

The identifier must be generated server-side.

The client must not be allowed to choose arbitrary internal database IDs
where the architecture does not require it.

---

## 14. Scan Creation Security

A user must not be able to submit:

```
severity
risk_score
scan_status
owner_id
created_at
```

as authoritative scan fields.

These values must be controlled by the backend.

---

## 15. Target Handling

The target URL submitted to the API must pass through Phase 03.

```
Client Target
     |
     v
API Validation
     |
     v
Phase 03 Target Validator
     |
     +---- BLOCK
     |
     v
Validated Target
```

No API endpoint may bypass the target-security layer.

---

## 16. Scan Execution

The scan manager orchestrates:

```
Target Validation
      |
      v
Phase 04 Scanner
      |
      v
Phase 05 Finding Engine
      |
      v
Phase 05 Risk Engine
      |
      v
Persistence
```

---

## 17. Scan Manager

Suggested component:

```
app/services/scan_manager.py
```

Responsibilities:

- create scan
- update scan state
- execute scanner
- process findings
- calculate risk
- persist results
- handle failures
- finalize scan
- maintain lifecycle consistency

The scan manager should not contain detailed TLS/header detection logic.

---

## 18. Service Layer

Recommended architecture:

```
API Route
    |
    v
Scan Service
    |
    v
Scan Manager
    |
    +--> Target Validator
    |
    +--> Scanner
    |
    +--> Finding Engine
    |
    +--> Risk Engine
    |
    v
Repositories
    |
    v
Database
```

This keeps API routes thin and maintainable.

---

## 19. API Routes

Suggested structure:

```
app/
└── api/
    └── routes/
        ├── health.py
        ├── auth.py
        └── scans.py
```

Exact route structure must follow Phase 01 and existing project architecture.

---

## 20. Scan Repository

The repository layer from Phase 02 should be used.

Suggested operations:

```
create_scan()
get_scan()
update_scan_status()
list_scans()
delete_scan()
```

Only operations actually required by the project should be implemented.

---

## 21. Scan Result Persistence

After successful scanning:

```
Scan
 |
 +--> Scan Result
 |
 +--> TLS Result
 |
 +--> HTTP Result
 |
 +--> Findings
 |
 +--> Risk Score
```

All persistence must respect the schema defined in:

```
Docs/DATABASE.md
```

Do not create duplicate tables or alternative result structures.

---

## 22. Transaction Handling

Persistence of related scan results should use appropriate database
transactions.

Example:

```
Start Transaction
       |
       +--> Save Scan Result
       +--> Save Findings
       +--> Save Risk Score
       |
       v
Commit
```

If a critical persistence operation fails:

```
Rollback
```

must be considered according to the transaction design.

---

## 23. Partial Persistence

The implementation must avoid leaving misleading scan records.

Example:

```
Scan = COMPLETED
Findings = Missing
Risk = Missing
```

must not occur unless explicitly supported by the data model.

A scan should only be marked completed after all required result
persistence succeeds.

---

## 24. Scan Status Updates

Typical lifecycle:

```
Create
  |
  v
QUEUED
  |
  v
RUNNING
  |
  v
Scanner
  |
  v
Finding Engine
  |
  v
Risk Engine
  |
  v
Persist
  |
  v
COMPLETED
```

Failures must produce:

```
FAILED
```

with safe structured error information.

---

## 25. Failure Handling

Possible failures:

- Target validation failure
- DNS failure
- Network timeout
- TLS failure
- HTTP failure
- Scanner module failure
- Finding processing failure
- Database failure
- Unexpected application error

The API must return appropriate HTTP responses without leaking internal
implementation details.

---

## 26. Error Response

API errors should have a consistent structure.

Conceptual:

```json
{
  "error": {
    "code": "SCAN_NOT_FOUND",
    "message": "The requested scan was not found.",
    "request_id": "..."
  }
}
```

Exact schema must follow Docs/API.md.

---

## 27. Information Disclosure

Do not expose:

- stack traces
- database credentials
- SQL queries
- internal filesystem paths
- environment variables
- API keys
- private network information
- internal service topology

in normal API responses.

Detailed errors should remain in controlled server logs.

---

## 28. HTTP Status Codes

Use appropriate status codes according to API specification.

Typical examples:

```
200 OK
201 Created
202 Accepted
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
500 Internal Server Error
```

Do not use status codes arbitrarily.

---

## 29. Scan Retrieval

Conceptual endpoint:

```
GET /api/v1/scans/{scan_id}
```

Response may contain:

- Scan metadata
- Status
- Target
- Timestamps
- Summary
- Risk result
- Finding counts

Exact response must follow Docs/API.md.

---

## 30. Scan History

Users should be able to retrieve their authorized scan history.

Conceptual:

```
GET /api/v1/scans
```

Filtering may include:

- status
- date range
- risk level

Only documented filters should be implemented.

---

## 31. Pagination

Scan history must use bounded pagination.

Example concept:

```
page
page_size
```

or cursor-based pagination if specified by the architecture.

Never return unlimited historical scan records.

---

## 32. Pagination Limits

The server must enforce a maximum page size.

Example:

```
Requested:
page_size = 1000000

Result:
Rejected or capped
```

The exact maximum must come from project configuration.

---

## 33. Finding Retrieval

A scan's findings should be retrievable through an API endpoint if
specified.

Conceptual:

```
GET /api/v1/scans/{scan_id}/findings
```

Only findings belonging to an authorized scan may be returned.

---

## 34. Risk Retrieval

Conceptual:

```
GET /api/v1/scans/{scan_id}/risk
```

Risk data must come from the authoritative Phase 05 Risk Engine result.

The API must never calculate risk independently.

---

## 35. Server-Authoritative Results

The client must never be trusted for:

- finding severity
- risk score
- risk level
- scan owner
- scan status
- scan timestamps

These values originate from the backend.

---

## 36. Rate Limiting

Scan creation is a resource-intensive operation.

Rate limiting must protect:

```
POST /scans
```

from abuse.

The exact limits must follow:

```
Docs/SECURITY.md
Docs/DEPLOYMENT.md
```

---

## 37. Resource Protection

The scan manager must prevent uncontrolled resource consumption.

Controls may include:

- maximum concurrent scans
- request rate limits
- scan timeout
- connection limits
- database connection limits
- response size limits

Exact values must be configuration-driven.

---

## 38. Duplicate Scan Requests

If the API supports idempotency, duplicate requests should be handled
according to the API specification.

If idempotency is not implemented:

- avoid accidental duplicate execution where practical
- do not silently merge unrelated scans

The behavior must be documented.

---

## 39. Scan Cancellation

If cancellation is supported:

```
RUNNING
   |
   v
CANCEL REQUEST
   |
   v
CANCELLED
```

Cancellation must be safe.

A completed scan cannot be cancelled.

A failed scan cannot be cancelled.

---

## 40. Cancellation Safety

Cancellation must not leave:

- Database corruption
- Partial misleading results
- Orphaned resources

Resource cleanup must occur even when cancellation happens.

---

## 41. Background Execution

If the current architecture supports asynchronous execution,
scan execution may be moved outside the request lifecycle.

Conceptually:

```
POST /scans
    |
    v
Create QUEUED Scan
    |
    v
Background Execution
    |
    v
RUNNING
    |
    v
COMPLETED
```

The implementation must follow the architecture already defined by the
project.

Do not introduce a large task queue framework unless required.

---

## 42. Synchronous Execution

If the MVP architecture intentionally uses synchronous execution:

```
POST /scans
    |
    v
Execute Scan
    |
    v
Return Result
```

the implementation must still enforce:

- timeout
- resource limits
- error handling
- rate limiting

The architecture must remain extensible for future background execution.

---

## 43. Request IDs

Every API request should have a request identifier.

Concept:

```
Request
  |
  +--> request_id
  |
  +--> logs
  |
  +--> error response
```

This enables troubleshooting without exposing sensitive information.

---

## 44. Logging

Log important scan lifecycle events:

- scan created
- scan started
- scan completed
- scan failed
- scan cancelled
- result persistence completed

Logs must not contain secrets.

---

## 45. Audit Logging

Security-sensitive actions may be written to the audit log defined in
the database model.

Examples:

- scan created
- scan cancelled
- scan deleted
- unauthorized scan access

Exact audit events must follow the project's security specification.

---

## 46. API Validation

Pydantic schemas should validate request bodies.

Reject:

- missing target
- malformed target
- oversized input
- unexpected values
- invalid pagination
- invalid filters

Do not rely exclusively on frontend validation.

---

## 47. Input Size Limits

API input must be bounded.

Do not allow:

- Extremely long target URLs
- Huge JSON payloads
- Huge query parameters

without appropriate limits.

---

## 48. SQL Injection Protection

API parameters must never be concatenated directly into SQL.

Use:

- SQLAlchemy ORM
- Parameterized Queries
- Repository Layer

Avoid:

```
"SELECT ... WHERE id = " + user_input
```

---

## 49. Authorization Query Design

Where practical, ownership filtering should happen at the database query
level.

Concept:

```
SELECT scan
WHERE scan_id = ?
AND user_id = ?
```

rather than:

```
SELECT scan
WHERE scan_id = ?

then manually check ownership later
```

This reduces accidental data exposure.

---

## 50. API Response Design

Responses should be:

- predictable
- versioned
- documented
- minimal
- security-conscious

Do not return internal database models directly.

Use response schemas.

---

## 51. API Versioning

API should use the versioning strategy established in Phase 01/API docs.

Example:

```
/api/v1/
```

Future breaking changes should be introduced through a new version
rather than silently changing existing responses.

---

## 52. Suggested Schemas

Possible structure:

```
app/
└── schemas/
    ├── scan.py
    ├── scan_result.py
    ├── finding.py
    ├── risk.py
    └── common.py
```

Use existing Phase 01/02/05 models where appropriate.

Avoid duplicate representations of the same domain object.

---

## 53. Suggested Services

```
app/
└── services/
    ├── scan_manager.py
    └── scan_service.py
```

Responsibilities should remain clearly separated.

---

## 54. Suggested API Structure

```
app/
└── api/
    └── routes/
        ├── health.py
        └── scans.py
```

Authentication routes should remain in their established module.

---

## 55. Scan Processing Pipeline

The complete Phase 06 pipeline:

```
API
 |
 v
Auth
 |
 v
Validate Request
 |
 v
Create Scan
 |
 v
Target Security
 |
 v
Scanner
 |
 v
Findings
 |
 v
Risk
 |
 v
Persist
 |
 v
Response
```

---

## 56. Database Consistency

The scan manager must preserve relationships defined in:

```
Docs/DATABASE.md
```

Foreign keys and transactions must remain consistent.

Do not bypass repositories unless the architecture explicitly permits it.

---

## 57. Security Boundary Preservation

The API must not provide alternate routes around security controls.

For example:

```
POST /scans
    |
    v
Target Validator
```

and not:

```
POST /special-scan
    |
    v
Direct HTTP Request
```

Every scan path must use the same security boundary.

---

## 58. Testing Strategy

Phase 06 requires:

- API Unit Tests
- Service Tests
- Repository Tests
- Authentication Tests
- Authorization Tests
- Scan Lifecycle Tests
- Integration Tests
- Security Tests
- Regression Tests

---

## 59. Authentication Tests

Test:

- authenticated request
- unauthenticated request
- invalid authentication
- expired authentication where applicable

Expected responses must follow API specification.

---

## 60. Authorization Tests

Create:

```
User A
User B
```

and verify:

```
User A -> Scan A = ALLOW
User A -> Scan B = DENY
User B -> Scan B = ALLOW
```

This test is mandatory.

---

## 61. Scan Lifecycle Tests

Test:

```
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
```

Also test invalid transitions.

Example:

```
COMPLETED -> RUNNING
```

must be rejected.

---

## 62. Scan Creation Tests

Test:

- valid target
- invalid target
- blocked target
- malformed request
- unauthorized request
- rate limit
- duplicate request behavior

---

## 63. Integration Test

Run the complete controlled pipeline:

```
API Request
    |
    v
Target Validation
    |
    v
Scanner
    |
    v
Finding Engine
    |
    v
Risk Engine
    |
    v
MySQL
    |
    v
API Response
```

Verify that database records match the returned result.

---

## 64. Failure Integration Tests

Simulate:

- DNS failure
- TLS failure
- HTTP timeout
- Scanner failure
- Finding failure
- Risk failure
- Database failure

Verify correct scan status and safe API response.

---

## 65. Database Transaction Tests

Test:

```
Successful persistence -> COMMIT

Persistence failure -> ROLLBACK
```

Verify that partial or inconsistent records are not silently marked as
completed.

---

## 66. Security Tests

Test:

- unauthorized scan access
- ID manipulation
- invalid authentication
- oversized requests
- invalid pagination
- SQL injection attempts
- SSRF bypass attempts
- blocked targets
- rate limiting
- information disclosure
- sensitive error leakage

All security tests must remain controlled and authorized.

---

## 67. API Contract Tests

Verify that API responses match:

```
Docs/API.md
```

Check:

- field names
- data types
- status codes
- error format
- required fields
- optional fields

---

## 68. Regression Tests

After Phase 06:

```
Phase 01 tests
Phase 02 tests
Phase 03 tests
Phase 04 tests
Phase 05 tests
Phase 06 tests
```

must remain green.

---

## 69. Performance

The API must remain responsive under normal usage.

Important controls:

- database connection pooling
- bounded scan concurrency
- request timeout
- scan timeout
- pagination
- efficient queries
- indexed ownership filters

Do not optimize prematurely without measurements.

---

## 70. Observability

The scan manager should expose enough information for debugging:

```
scan_id
request_id
status
start_time
completion_time
failure_code
```

Avoid exposing internal implementation details through public APIs.

---

## 71. Suggested Project Structure

```
app/
├── api/
│   └── routes/
│       ├── health.py
│       └── scans.py
│
├── schemas/
│   ├── scan.py
│   ├── scan_result.py
│   ├── finding.py
│   └── risk.py
│
├── services/
│   ├── scan_manager.py
│   └── scan_service.py
│
└── repositories/
    └── scan_repository.py

tests/
├── api/
│   └── test_scans.py
│
├── services/
│   ├── test_scan_manager.py
│   └── test_scan_service.py
│
└── integration/
    └── test_scan_pipeline.py
```

Exact paths must follow the existing project architecture.

---

## 72. Acceptance Criteria

Phase 06 is accepted only when:

- [ ] Scan creation API is implemented
- [ ] Authentication is enforced
- [ ] Authorization is enforced
- [ ] Target validation is mandatory
- [ ] Scan lifecycle is implemented
- [ ] Scan manager is implemented
- [ ] Scanner integration works
- [ ] Finding Engine integration works
- [ ] Risk Engine integration works
- [ ] Results are persisted
- [ ] Scan retrieval works
- [ ] Scan history works
- [ ] Pagination works
- [ ] Findings can be retrieved
- [ ] Risk result can be retrieved
- [ ] Error responses are consistent
- [ ] Request IDs are supported
- [ ] Rate limiting is applied
- [ ] Resource limits are enforced
- [ ] Object-level authorization works
- [ ] Transactions are handled correctly
- [ ] Sensitive information is not exposed
- [ ] API contract tests pass
- [ ] Security tests pass
- [ ] Integration tests pass
- [ ] Regression tests pass

---

## 73. Definition of Done

Phase 06 is complete when the complete backend workflow works:

```
Authenticated User
       |
       v
Create Scan
       |
       v
Target Validation
       |
       v
Security Scanner
       |
       v
Finding Engine
       |
       v
Risk Engine
       |
       v
MySQL Persistence
       |
       v
API Retrieval
```

The frontend must be able to consume this API without implementing
security logic itself.

---

## 74. Expected Deliverables

At the end of Phase 06:

- Scan API
- Scan Manager
- Scan Service
- Scan Lifecycle
- Scan Repository Integration
- Request Schemas
- Response Schemas
- Authentication Integration
- Authorization
- Pagination
- Error Handling
- Rate Limiting
- Request IDs
- Database Transactions
- Scan Integration
- API Tests
- Security Tests
- Integration Tests
- Documentation Updates

---

## 75. AI Coding Agent Prompt

```
You are implementing PHASE 06 of the
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
Phases/PHASE_05_FINDING_RISK.md
Phases/PHASE_06_API_SCAN_MANAGER.md

TASK:

Implement ONLY PHASE 06 — SCAN MANAGEMENT & API.

PRIMARY GOAL:

Connect the existing secure target validation, scanner,
Finding Engine, Risk Engine, and database into a secure
backend scan-management workflow.

ARCHITECTURE:

API
 ->
Authentication
 ->
Request Validation
 ->
Scan Manager
 ->
Phase 03 Target Security
 ->
Phase 04 Scanner
 ->
Phase 05 Finding Engine
 ->
Phase 05 Risk Engine
 ->
Repositories
 ->
MySQL

IMPORTANT:

Do not duplicate security logic from previous phases.

Do not implement alternate scanning paths.

Every scan must use the Phase 03 target-security boundary.

IMPLEMENT:

1. Scan creation API.
2. Scan lifecycle management.
3. Scan Manager.
4. Scan Service.
5. Scan repository integration.
6. Scan status handling.
7. Scan result persistence.
8. Finding persistence.
9. Risk persistence.
10. Scan retrieval.
11. Scan history.
12. Pagination.
13. Authentication integration.
14. Object-level authorization.
15. Request validation.
16. Response schemas.
17. Structured API errors.
18. Request IDs.
19. Rate limiting integration.
20. Resource limits.
21. Transaction handling.
22. Comprehensive tests.

SCAN STATES:

Use the project-defined states:

QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED

Implement valid state transitions only.

AUTHORIZATION:

A user must only access scans they are authorized to access.

Never trust a scan ID alone.

Ownership/permission filtering should be enforced securely.

TARGET SECURITY:

Every target must pass Phase 03 validation.

Never allow:

API -> raw URL -> HTTP client

Correct:

API -> Phase 03 -> Safe Target -> Scanner

SCANNER:

Use Phase 04 scanner.

Do not duplicate TLS, HTTP header, cookie, or redirect detection
inside API/service code.

FINDINGS:

Use Phase 05 Finding Engine.

Do not calculate severity in API code.

RISK:

Use Phase 05 Risk Engine.

Never accept risk_score or risk_level from the client.

DATABASE:

Use the repositories and schema defined in Phase 02 and Docs/DATABASE.md.

Use transactions where required.

Do not mark a scan COMPLETED before required results have been
successfully persisted.

ERROR HANDLING:

Handle safely:

- invalid target
- blocked target
- DNS failure
- TLS failure
- HTTP failure
- scanner failure
- finding failure
- risk failure
- database failure
- authorization failure
- authentication failure
- timeout

Do not expose:

- stack traces
- SQL
- credentials
- environment variables
- internal filesystem paths
- secrets
- private implementation details

RATE LIMITING:

Protect scan creation from abuse.

Use existing security configuration where available.

Do not invent arbitrary limits if documented configuration already exists.

PAGINATION:

Scan history must be bounded.

Never return unlimited records.

SECURITY:

Test:

- unauthorized scan access
- scan ID manipulation
- authentication failures
- SSRF bypass attempts
- blocked targets
- oversized input
- invalid pagination
- SQL injection
- rate limiting
- sensitive error disclosure

Use controlled test fixtures only.

DO NOT IMPLEMENT:

- frontend/dashboard
- AI
- reports
- notifications
- scheduled scans
- advanced background job systems
- deployment automation

These belong to later phases.

PRESERVE EXISTING FUNCTIONALITY.

Do not rewrite Phase 01–05 unnecessarily.

Do not introduce new frameworks.

Use the existing architecture and coding conventions.

TESTING:

Run:

1. API tests
2. service tests
3. repository tests
4. authentication tests
5. authorization tests
6. lifecycle tests
7. integration tests
8. security tests
9. full regression suite

Verify the complete controlled pipeline:

API
 -> Target Validation
 -> Scanner
 -> Findings
 -> Risk
 -> MySQL
 -> API Response

After implementation:

1. Run formatter/linter if configured.
2. Run all Phase 06 tests.
3. Run all existing project tests.
4. Fix regressions.
5. Verify application startup.
6. Verify imports.
7. Verify type checking where configured.
8. Verify API contracts against Docs/API.md.
9. Report all changed files.
10. Report exact test results.
11. Report unresolved issues.

Do not claim completion without actually running the tests.

The implementation must be secure, modular, deterministic,
production-oriented, and maintainable.
```

---

## 76. Phase Completion Record

After implementation, update:

```
Phase: 06
Status: Completed / Pending

Implemented:
- Scan API
- Scan Manager
- Scan Service
- Scan Lifecycle
- Authentication
- Authorization
- Persistence
- Scan History
- Pagination
- Error Handling
- Rate Limiting
- Request IDs

Tests:
- API Tests: ___
- Service Tests: ___
- Repository Tests: ___
- Security Tests: ___
- Integration Tests: ___
- Regression Tests: ___
- Total: ___

Result:
PASS / FAIL

Known Issues:
- None / ...

Approved For:
Phase 07 — Frontend & Dashboard
```

---

## 77. Transition To Phase 07

After Phase 06, the backend scanning pipeline is accessible through
secure APIs.

The architecture becomes:

```
User
 |
 v
Frontend
 |
 v
Phase 06 API
 |
 v
Scan Manager
 |
 +--> Phase 03
 +--> Phase 04
 +--> Phase 05
 |
 v
MySQL
```

Phase 07 will build the user-facing security dashboard.

It will consume the API rather than directly accessing the database.

---

### FINAL PRINCIPLE

The API orchestrates the security pipeline.
It does not replace the security pipeline.

The frontend must never be trusted with security decisions,
and the API must never bypass the deterministic security engines.