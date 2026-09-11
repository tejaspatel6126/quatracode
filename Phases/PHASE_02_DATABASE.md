# Phase 02 — Database & Data Layer

## 1. Phase Overview

### Phase Name

Database & Data Layer

### Phase Number

02

### Objective

Implement the complete MySQL database layer for the
AI-Powered Web Security Configuration Auditor.

This phase converts the database foundation created in
Phase 01 into a functional, structured and migration-managed
data layer.

The database must support:

- Users
- Authentication-related data
- Scans
- Scan results
- TLS results
- HTTP results
- Findings
- Risk scores
- AI summaries
- Audit information

The implementation must follow `Docs/DATABASE.md`.

---

## 2. Phase Goal

At the end of this phase:

```
FastAPI
   |
   v
SQLAlchemy
   |
   v
Repositories
   |
   v
MySQL
   |
   v
Persistent Project Data
```

The application must be able to create, read, update and
delete the required database records through a clean data
access layer.

## 3. Documents That Must Be Followed

Before implementation, review:

- Docs/SRS.md
- Docs/ARCHITECTURE.md
- Docs/DATABASE.md
- Docs/API.md
- Docs/SECURITY.md
- Docs/TESTING.md
- Docs/DEPLOYMENT.md
- Docs/ROADMAP.md
- Phases/PHASE_01_FOUNDATION.md
- Phases/PHASE_02_DATABASE.md

Docs/DATABASE.md is the primary source of truth for the
database schema.

## 4. Implementation Rules

The implementation agent must:

- Preserve Phase 01 functionality.
- Follow the documented database architecture.
- Use SQLAlchemy ORM.
- Use Alembic migrations.
- Use parameterized database operations.
- Keep database logic separate from API routes.
- Keep repositories separate from business services.
- Avoid raw SQL unless genuinely required.
- Never hard-code credentials.
- Never commit database passwords.
- Never silently change the documented schema.

## 5. Database Technology

Use:

- MySQL 8.x
- SQLAlchemy
- Alembic

Recommended architecture:

```
API
 |
 v
Service
 |
 v
Repository
 |
 v
SQLAlchemy
 |
 v
MySQL
```

Routes should not directly execute database queries.

## 6. Database Configuration

The database connection must be configurable through
environment variables.

Preferred approach:

```
DATABASE_URL
```

or equivalent documented variables.

Example:

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DB_NAME
```

The actual production credentials must never be placed inside
source code.

## 7. Database Naming

Use a consistent naming convention.

Recommended:

```
Tables: lowercase snake_case
Columns: lowercase snake_case
Primary keys: id
Foreign keys: <table>_id
```

Examples:

```
users
scans
scan_results
findings
risk_scores
ai_summaries
audit_logs
```

Use the exact names defined in Docs/DATABASE.md if they
differ from these examples.

## 8. Core Entity Model

The database should conceptually represent:

```
User
 |
 +---- Scan
        |
        +---- Scan Result
        |
        +---- TLS Result
        |
        +---- HTTP Result
        |
        +---- Finding
        |
        +---- Risk Score
        |
        +---- AI Summary
        |
        +---- Audit Data
```

The exact relationships must follow Docs/DATABASE.md.

## 9. User Model

Implement the user entity required by the application.

Minimum conceptual fields:

```
id
email
password_hash
is_active
created_at
updated_at
```

Additional fields may be included if defined by the database
specification.

Requirements:

- Email must be uniquely constrained.
- Passwords must never be stored in plaintext.
- Password hashes must be treated as sensitive data.
- User records must have appropriate indexes.

Authentication behavior itself belongs primarily to later
application phases.

This phase only establishes the persistence model.

## 10. Scan Model

Implement the scan entity.

A scan represents one authorized web security audit request.

Conceptual fields:

```
id
user_id
target_url
status
started_at
completed_at
created_at
updated_at
```

Possible statuses:

```
queued
running
completed
failed
cancelled
```

The exact status values must match the application contract.

Use a stable identifier such as UUID if specified by the
architecture.

## 11. Target URL Storage

Store the target URL required to reproduce and display the
scan.

Requirements:

- Use an appropriate column size.
- Validate the URL at the application layer.
- Do not assume database validation replaces SSRF protection.
- Do not use the database value directly for network
  connections without passing through the scanner's security
  validation layer.

Important:

```
Database storage is not target authorization.
```

## 12. Scan Result Model

Create the structure for storing scanner results.

Conceptually:

```
Scan
 |
 v
Scan Result
 |
 +-- TLS data
 +-- HTTP data
 +-- Redirect data
 +-- Cookie data
 +-- Content data
```

The exact fields must follow Docs/DATABASE.md.

Avoid putting unrelated scanner data into one unstructured
large text column when structured storage is defined.

## 13. TLS Result Model

Create a dedicated persistence structure for TLS analysis.

Potential data:

```
certificate_valid
certificate_expiry
hostname_valid
chain_valid
tls_version
cipher
certificate_subject
certificate_issuer
```

Only fields defined by the database specification should be
implemented.

Sensitive certificate or connection metadata should not be
stored unnecessarily.

## 14. HTTP Result Model

Create the HTTP analysis persistence structure.

Potential information:

```
status_code
http_version
final_url
redirect_count
response_headers
```

Header storage must be designed carefully.

Do not unnecessarily store:

- Authorization headers
- Session tokens
- Cookies containing secrets
- API keys
- Sensitive personal data

Sensitive values must be redacted before persistence if they
are captured.

## 15. Finding Model

Implement the security finding entity.

Conceptual fields:

```
id
scan_id
rule_id
title
category
severity
confidence
description
evidence
recommendation
created_at
```

Potential severity values:

```
critical
high
medium
low
info
```

Use the exact values defined by the scanner specification.

The finding model must support deterministic findings.

## 16. Finding Relationships

A scan may contain multiple findings.

Relationship:

```
One Scan
   |
   +---- Finding
   +---- Finding
   +---- Finding
   +---- Finding
```

Every finding must belong to a valid scan.

Deleting a scan must follow the documented retention and
cascade strategy.

Do not accidentally create orphan findings.

## 17. Risk Score Model

Create the persistence structure for risk calculation.

Conceptual fields:

```
id
scan_id
score
risk_level
created_at
```

Potential risk levels:

```
critical
high
medium
low
minimal
```

The exact levels must follow the risk engine specification.

Important:

```
The database stores the calculated risk. It does not
calculate the risk.
```

Risk calculation belongs to the deterministic risk engine.

## 18. AI Summary Model

Create the persistence structure for AI-generated
explanations.

Potential fields:

```
id
scan_id
summary
model
status
created_at
updated_at
```

The database must clearly distinguish between:

```
Security Findings
```

and:

```
AI Explanation
```

AI-generated text must never overwrite authoritative finding
data.

## 19. Audit Log Model

If defined by the database architecture, create an audit log
entity.

Potential information:

```
id
user_id
action
resource_type
resource_id
request_id
metadata
created_at
```

Audit records should help answer:

- Who performed the action?
- What action occurred?
- Which resource was affected?
- When did it happen?
- Which request caused it?

Never store secrets inside audit metadata.

## 20. Relationships

The database relationships should follow the documented
architecture.

Conceptually:

```
User
 |
 +------< Scan
            |
            +------< Finding
            |
            +------1 Risk
            |
            +------1 AI Summary
            |
            +------1 Result
```

The exact cardinality must match Docs/DATABASE.md.

## 21. Foreign Keys

Use proper foreign key constraints.

Examples:

```
scans.user_id
    -> users.id

findings.scan_id
    -> scans.id

risk_scores.scan_id
    -> scans.id

ai_summaries.scan_id
    -> scans.id
```

Foreign key behavior must be intentionally selected.

Do not use unrestricted cascading deletes without considering
audit and data-retention requirements.

## 22. Indexing Strategy

Create indexes for frequently queried fields.

Likely candidates:

```
users.email
scans.user_id
scans.status
scans.created_at
findings.scan_id
findings.severity
risk_scores.scan_id
audit_logs.user_id
audit_logs.created_at
```

Do not create indexes on every column.

Indexes should support real query patterns.

## 23. Unique Constraints

Use unique constraints where required.

Examples:

```
users.email
```

If the architecture requires one risk score or AI summary
per scan, enforce the intended relationship appropriately.

Do not rely solely on application-level checks when a database
constraint can safely enforce uniqueness.

## 24. Timestamps

Use consistent timestamp handling.

Recommended fields:

```
created_at
updated_at
started_at
completed_at
```

Timestamps should be stored consistently and converted for
display at the application boundary.

Avoid mixing timezone-naive and timezone-aware timestamps
without an explicit strategy.

## 25. SQLAlchemy Models

Create ORM models under the documented model package.

Example:

```
app/
|
+-- models/
|   +-- user.py
|   +-- scan.py
|   +-- scan_result.py
|   +-- finding.py
|   +-- risk_score.py
|   +-- ai_summary.py
|   +-- audit_log.py
```

The exact filenames may be adjusted to the existing project
architecture.

Avoid putting all models into one oversized file.

## 26. Model Base

All models should use the centralized SQLAlchemy declarative
base created during Phase 01.

Concept:

```
Base
 |
 +-- User
 +-- Scan
 +-- Finding
 +-- RiskScore
 +-- AISummary
 +-- AuditLog
```

Do not create multiple unrelated ORM bases.

## 27. Repository Layer

Create repository classes or functions for database access.

Recommended structure:

```
app/
|
+-- repositories/
    |
    +-- user_repository.py
    +-- scan_repository.py
    +-- finding_repository.py
    +-- risk_repository.py
    +-- ai_repository.py
    +-- audit_repository.py
```

Repositories should handle:

- Create
- Read
- Update
- Delete
- Filter
- Pagination where required

Repositories should not contain HTTP logic.

## 28. Service vs Repository Responsibility

Use this separation:

```
Service
 |
 | Business Rules
 v
Repository
 |
 | Database Operations
 v
MySQL
```

Example:

The service decides:

```
Whether a scan can be created.
```

The repository performs:

```
Insert scan record into database.
```

Do not mix these responsibilities.

## 29. Transaction Management

Database operations must use proper transactions.

Concept:

```
Begin
  |
  v
Database Operations
  |
  +---- Success --> Commit
  |
  +---- Failure --> Rollback
```

Never leave failed transactions open.

Ensure sessions are properly closed.

## 30. Scan Creation Transaction

A future scan creation workflow may involve:

```
Create Scan
    |
    v
Commit
```

Do not create incomplete related records before the scan
transaction is safely established.

Scanner-specific result persistence will be implemented in
later phases.

## 31. Migration

Create the first complete schema migration for Phase 02.

Migration should:

- Create required tables.
- Create primary keys.
- Create foreign keys.
- Create unique constraints.
- Create indexes.
- Create required enums or equivalent constraints.
- Support clean rollback where practical.

Migration must be reproducible.

## 32. Migration Verification

Verify:

```
Empty Database
      |
      v
Alembic Upgrade
      |
      v
Complete Schema
```

Then:

```
Complete Schema
      |
      v
Alembic Downgrade
      |
      v
Previous State
```

Do not modify the database manually and assume the migration
system is correct.

## 33. Database Security

The application database must follow least privilege.

Application user should have only the permissions required by
the application.

Do not use:

```
root
```

as the production application database user.

Database credentials must be provided through secure
environment configuration.

## 34. SQL Injection Protection

All database access must use:

- SQLAlchemy parameterization
- ORM queries
- Bound parameters

Never construct SQL using untrusted string concatenation.

Bad:

```
"SELECT * FROM users WHERE email = '" + email + "'"
```

Preferred:

```
SQLAlchemy query
+
bound parameter
```

## 35. Sensitive Data Protection

The database must not unnecessarily store:

- Password plaintext
- API keys
- AI provider secrets
- Session secrets
- Authorization tokens
- Scanner credentials
- Raw sensitive cookies

If sensitive values are required for debugging or evidence,
they must be appropriately redacted.

## 36. Database Connection Security

Production database connections should use:

- Private network access
- Firewall restrictions
- Strong credentials
- TLS where appropriate
- Least-privilege accounts

The database should not be publicly exposed to the Internet.

## 37. Connection Pooling

SQLAlchemy should use a controlled connection pool.

Consider:

- Pool size
- Maximum overflow
- Connection timeout
- Connection recycling
- Pre-ping

Values should be configurable for different environments.

Do not blindly choose extremely large pool sizes.

## 38. Repository Testing

Create tests for:

**User**
- Create user
- Read user
- Duplicate email
- Update user
- Delete user where allowed

**Scan**
- Create scan
- Read scan
- Filter scans
- Status update
- Ownership filtering

**Finding**
- Create finding
- Retrieve findings
- Severity filtering
- Scan relationship

**Risk**
- Store risk score
- Retrieve risk score

**AI**
- Store AI summary
- Retrieve AI summary
- AI failure state

## 39. Database Integration Tests

Use an isolated test database.

Tests must not modify production data.

Recommended:

```
Test Database
     |
     v
Migration
     |
     v
Tests
     |
     v
Cleanup
```

Do not run destructive tests against a real production
database.

## 40. Migration Tests

Verify:

- Fresh migration succeeds.
- Tables exist.
- Foreign keys exist.
- Indexes exist.
- Constraints exist.
- Migration rollback works where supported.
- Re-running migration does not corrupt schema.

## 41. Relationship Tests

Test important relationships.

Example:

```
User
 |
 v
Scan
 |
 +--> Finding
 +--> Risk
 +--> AI Summary
```

Verify:

- Valid relationships work.
- Invalid foreign keys fail safely.
- Orphan records cannot be created unintentionally.
- Delete behavior matches documentation.

## 42. Pagination Foundation

Repositories that return potentially large collections should
support pagination where required.

Concept:

```
Request
 |
 +-- page
 +-- limit
 |
 v
Repository
 |
 v
Limited Result Set
```

Never load an unbounded number of historical findings into
memory unnecessarily.

## 43. Query Performance

Check the generated query patterns for:

- Scan history
- Finding lists
- Dashboard summaries
- User-specific scans

Use indexes appropriately.

Avoid N+1 query patterns when relationships are loaded.

## 44. Error Handling

Database errors must be translated into safe application
errors.

Do not expose raw MySQL errors to users.

Bad:

```
MySQL IntegrityError:
Duplicate entry '...'
```

Preferred:

```
A user with this email already exists.
```

Internal logs may contain controlled technical information.

## 45. Health Check Integration

Update the readiness check from Phase 01 so that it can verify
database connectivity.

Concept:

```
/api/v1/health/ready
        |
        v
Database Connection
        |
   +----+----+
   |         |
   v         v
 Ready    Not Ready
```

Do not expose database credentials or connection strings.

## 46. What Must NOT Be Implemented

Do not implement the following as complete features:

- TLS scanner
- HTTP scanner
- SSRF engine
- Finding detection rules
- Risk calculation logic
- AI provider integration
- Complete frontend dashboard
- Continuous monitoring
- Alerts
- CI/CD integration

Those belong to later phases.

Database support for future entities is acceptable only where
required by the documented schema.

## 47. Backward Compatibility

After implementation:

- Existing Phase 01 tests must pass.
- Existing endpoints must continue working.
- Existing configuration must continue working.
- Existing project structure must not be unnecessarily changed.

If a change is required, make the smallest safe change.

## 48. Verification Commands

Run:

```
pytest
```

Then run migrations:

```
alembic upgrade head
```

Verify database connectivity.

Inspect the resulting schema.

Then test rollback if supported:

```
alembic downgrade -1
```

Finally restore the latest schema:

```
alembic upgrade head
```

Use the exact commands defined by the project environment
if they differ.

## 49. Acceptance Criteria

Phase 02 is accepted only if:

**Database**
- [ ] MySQL connection works.
- [ ] SQLAlchemy models exist.
- [ ] Relationships are correct.
- [ ] Foreign keys are correct.
- [ ] Indexes are implemented.
- [ ] Unique constraints are implemented.
- [ ] Timestamp strategy is consistent.

**Migrations**
- [ ] Alembic migration exists.
- [ ] Fresh database migration succeeds.
- [ ] Schema can be reproduced.
- [ ] Rollback is verified where applicable.

**Repository**
- [ ] Repository layer exists.
- [ ] CRUD operations work.
- [ ] Transactions are handled correctly.
- [ ] Pagination is supported where required.

**Security**
- [ ] No hard-coded database credentials.
- [ ] No plaintext passwords.
- [ ] SQL injection protections are in place.
- [ ] Sensitive values are not unnecessarily stored.
- [ ] Production root database access is not required.

**Testing**
- [ ] Repository tests pass.
- [ ] Relationship tests pass.
- [ ] Migration tests pass.
- [ ] Database integration tests pass.
- [ ] All Phase 01 tests still pass.

## 50. Definition of Done

Phase 02 is complete when:

```
Database
   |
   v
Models
   |
   v
Relationships
   |
   v
Repositories
   |
   v
Transactions
   |
   v
Migrations
   |
   v
Tests
   |
   v
Security Verification
   |
   v
PHASE 02 COMPLETE
```

The application must have a reliable persistence layer ready
for the security scanner.

## 51. Expected Deliverables

Expected additions/modifications:

```
app/
|
+-- db/
|
+-- models/
|
+-- repositories/
|
+-- schemas/
|
+-- ...

migrations/
|
+-- versions/
|
    +-- <phase_02_migration>.py

tests/
|
+-- unit/
|   +-- repositories/
|
+-- integration/
|   +-- database/
```

The exact structure must follow the existing repository.

## 52. AI Coding Agent Prompt

```
You are implementing Phase 02 — Database & Data Layer
of the AI-Powered Web Security Configuration Auditor.

First inspect the complete repository.

Read:

Docs/SRS.md
Docs/ARCHITECTURE.md
Docs/DATABASE.md
Docs/API.md
Docs/SECURITY.md
Docs/TESTING.md
Docs/DEPLOYMENT.md
Docs/ROADMAP.md

Phases/PHASE_01_FOUNDATION.md
Phases/PHASE_02_DATABASE.md
```

### Primary objective

```
Implement the complete MySQL persistence layer described by
Docs/DATABASE.md.

You must:

Inspect existing Phase 01 implementation.
Preserve working functionality.
Implement SQLAlchemy models.
Implement documented relationships.
Implement foreign keys.
Implement indexes.
Implement unique constraints.
Implement timestamps.
Implement repositories.
Implement transaction handling.
Create Alembic migrations.
Implement isolated database tests.
Integrate database connectivity into readiness checks.
Update README only where database setup documentation is
required.
```

### Architecture

```
Maintain:

API
 |
 v
Service
 |
 v
Repository
 |
 v
SQLAlchemy
 |
 v
MySQL

Do not place database queries directly inside API routes.
```

### Security

```
Never:

Hard-code database credentials.
Store plaintext passwords.
Use root as the production application database user.
Build SQL using string concatenation.
Store API keys or secrets.
Expose raw database errors to API users.
Expose database credentials through health endpoints.

Use SQLAlchemy parameterization and safe transaction handling.
```

### Scope restriction

```
Do NOT implement:

TLS scanner
HTTP scanner
SSRF protection engine
Finding detection
Risk calculation
AI provider integration
Continuous monitoring
Alerts
Enterprise features

Only implement database infrastructure required for this
phase.
```

### Existing functionality protection

```
Before changing files:

Inspect existing code.
Understand current architecture.
Run existing tests.
Reuse working Phase 01 infrastructure.
Avoid unnecessary rewrites.
Avoid deleting working files.
Avoid changing API contracts unnecessarily.
```

### Database implementation

```
Implement the entities defined in Docs/DATABASE.md.

Ensure:

Correct primary keys.
Correct foreign keys.
Correct relationships.
Correct indexes.
Correct constraints.
Correct timestamp handling.
Correct cascade behavior.
Correct nullable/non-nullable fields.

Do not invent schema fields when the documentation already
defines the required structure.
```

### Migration

```
Create an Alembic migration that can reproduce the schema
from an empty database.

Test:

Empty DB
  |
  v
alembic upgrade head
  |
  v
Schema Created

Then test rollback where applicable.
```

### Testing

```
Run all existing tests.

Add:

Model tests
Repository tests
Relationship tests
Constraint tests
Migration tests
Database integration tests

Use an isolated test database.

Never run destructive tests against production.
```

### Final verification

```
Verify:

Application startup.
Health endpoint.
Readiness endpoint.
Database connectivity.
Migration.
Repository operations.
Existing Phase 01 tests.

Fix failures introduced by the implementation.

Do not weaken tests to make them pass.
```

### Final response

```
Report:

Files created.
Files modified.
Database tables created.
Relationships created.
Indexes and constraints.
Migration details.
Repository implementation.
Tests executed.
Test results.
Security verification.
Known issues.
Confirmation whether Phase 02 is ready for Phase 03.

Do not claim completion if migrations, tests or application
startup are failing.
```

## 53. Phase Completion Record

Record the phase after implementation:

```
Phase:
02 — Database & Data Layer

Status:
[ ] Not Started
[ ] In Progress
[ ] Blocked
[ ] Complete

Models:
[ ]

Relationships:
[ ]

Repositories:
[ ]

Migration:
[ ]

Tests:
[ ]

Security Verification:
[ ]

Known Issues:
[ ]

Reviewed By:
[ ]

Date:
[ ]
```

## 54. Transition to Phase 03

Only start Phase 03 after Phase 02 is complete.

Phase 03 will implement the most security-sensitive part of
the platform:

```
User Target URL
      |
      v
URL Validation
      |
      v
DNS Resolution
      |
      v
IP Validation
      |
      v
SSRF Protection
      |
      v
Safe Scan Target
```

Phase 03 will establish the security boundary before the
scanner is allowed to make outbound network requests.

## 55. Final Principle

The database must remain a reliable source of persistent
application data.

It must not become the place where security decisions are
silently invented.

The correct architecture is:

```
Scanner
   |
   v
Finding Engine
   |
   v
Risk Engine
   |
   v
Repository
   |
   v
MySQL
```

The database stores security decisions and evidence; it
does not create them.