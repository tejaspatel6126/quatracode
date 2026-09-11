# Phase 01 — Foundation & Project Setup

## 1. Phase Overview

### Phase Name

Foundation & Project Setup

### Phase Number

01

### Objective

Establish a clean, secure and scalable foundation for the
AI-Powered Web Security Configuration Auditor.

This phase creates the base project structure, development
environment, FastAPI application, frontend foundation,
configuration system and initial application infrastructure.

No actual security scanning logic is implemented in this
phase.

The purpose is to create a stable foundation on which all
following phases can safely build.

---

## 2. Phase Goal

At the end of this phase, the project must have:

```
Project
  |
  +-- Backend
  +-- Frontend
  +-- Configuration
  +-- Database Layer
  +-- Security Base
  +-- Testing Base
  +-- Documentation
```

The application should start successfully and provide a
basic health endpoint.

## 3. Documents That Must Be Followed

Before implementation, review these documents:

- Docs/SRS.md
- Docs/ARCHITECTURE.md
- Docs/SECURITY.md
- Docs/API.md
- Docs/DATABASE.md
- Docs/TESTING.md
- Docs/DEPLOYMENT.md
- Docs/UI_UX.md
- Docs/AI_MODEL.md
- Docs/SCANNER_SPECIFICATION.md
- Docs/DEMO.md
- Docs/ROADMAP.md

These documents are the source of truth for the project.

If an implementation decision conflicts with the
documentation, review the documentation before making
changes.

## 4. Important Implementation Rule

The implementation agent must:

- Preserve existing functionality.
- Follow the documented architecture.
- Avoid unnecessary dependencies.
- Avoid unnecessary refactoring.
- Avoid changing documented API contracts.
- Avoid implementing future-phase functionality.
- Never bypass security controls for convenience.
- Keep code modular and testable.
- Keep configuration outside source code where appropriate.

Do not implement the scanner, AI service or complete
authentication system in this phase unless required only as
a minimal structural placeholder.

## 5. Technology Stack

**Backend**
- Python
- FastAPI
- Pydantic
- Uvicorn
- SQLAlchemy
- Alembic

**Database**
- MySQL 8.x

**Frontend**
- HTML
- CSS
- Vanilla JavaScript

No frontend framework is required for Phase 01.

**Testing**
- pytest
- pytest-asyncio
- HTTPX

**Version Control**
- Git

## 6. Prerequisites

Before starting implementation, verify:

- Python
- Git
- MySQL
- Node.js (only if required by tooling)
- Code Editor

Python should use a supported project version.

Recommended:

```
Python 3.11+
```

The exact production version must remain compatible with
the deployment documentation.

## 7. Project Structure

Create the following structure:

```
quatracode/
|
+-- app/
|   |
|   +-- api/
|   |   +-- routes/
|   |
|   +-- core/
|   |
|   +-- models/
|   |
|   +-- schemas/
|   |
|   +-- repositories/
|   |
|   +-- services/
|   |
|   +-- scanners/
|   |
|   +-- db/
|   |
|   +-- main.py
|
+-- frontend/
|   |
|   +-- index.html
|   +-- css/
|   +-- js/
|
+-- tests/
|
+-- migrations/
|
+-- Docs/
|
+-- Phases/
|
+-- .env.example
+-- .gitignore
+-- README.md
+-- requirements.txt
```

The exact structure may be adjusted if it conflicts with
the existing repository, but architectural separation must
be preserved.

## 8. Backend Foundation

Create the FastAPI application entry point.

Example responsibility:

```
app/main.py
```

The main application should:

- Create the FastAPI application.
- Register API routers.
- Configure application metadata.
- Configure middleware where required.
- Expose health endpoints.
- Initialize required infrastructure safely.

Do not place business logic directly inside `main.py`.

## 9. API Versioning

The API must use the documented versioning strategy.

Base path:

```
/api/v1
```

Initial endpoint:

```
GET /api/v1/health
```

Expected response should be simple and machine-readable.

Example:

```json
{
  "status": "ok"
}
```

The exact response schema should remain consistent with
Docs/API.md.

## 10. Readiness Endpoint

Create:

```
GET /api/v1/health/ready
```

This endpoint represents whether required application
dependencies are available.

It may eventually verify:

- Database connectivity
- Required configuration
- Required infrastructure

Do not expose:

- Passwords
- API keys
- Database credentials
- Internal secrets
- Sensitive infrastructure information

## 11. Configuration System

Create a centralized configuration system.

Configuration should support:

```
Environment Variables
        |
        v
Application Settings
        |
        v
Services
```

Configuration categories may include:

**Application**
```
APP_NAME
APP_ENV
DEBUG
```

**Database**
```
DATABASE_URL
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

**Security**
```
SECRET_KEY
ALLOWED_ORIGINS
```

**AI**

AI configuration should be added structurally but actual AI
integration belongs to Phase 08.

Never hard-code secrets.

## 12. Environment Files

Create:

```
.env.example
```

It may contain placeholders such as:

```
APP_ENV=development
DEBUG=false

DATABASE_URL=

SECRET_KEY=

ALLOWED_ORIGINS=
```

Do not put real credentials into `.env.example`.

Real `.env` files must not be committed to Git.

## 13. Git Ignore

Create or update:

```
.gitignore
```

It must exclude at minimum:

```
.env
.venv/
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.idea/
.vscode/
```

Also exclude generated secrets, local databases and other
environment-specific artifacts where applicable.

Do not blindly ignore source files or documentation.

## 14. Virtual Environment

Create a dedicated Python virtual environment.

Example:

```
python -m venv .venv
```

Activate it according to the operating system.

Windows PowerShell:

```
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```
source .venv/bin/activate
```

The project must run using the project's virtual environment
rather than relying on globally installed packages.

## 15. Dependency Management

Create:

```
requirements.txt
```

Initial dependencies should contain only packages required
for the foundation.

Expected categories:

- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- Alembic
- MySQL driver
- pytest
- pytest-asyncio
- HTTPX

Do not install large unrelated packages.

Every dependency should have a clear purpose.

## 16. Database Foundation

Create the database infrastructure layer.

Recommended separation:

```
app/
|
+-- db/
|   +-- session.py
|   +-- base.py
|
+-- models/
```

The database layer should provide:

- Engine creation
- Session management
- Base model configuration
- Connection handling
- Environment-based configuration

Do not implement all project models in this phase.

Database models will be implemented in Phase 02.

## 17. SQLAlchemy Configuration

Configure SQLAlchemy so that:

```
FastAPI
   |
   v
Database Session
   |
   v
SQLAlchemy
   |
   v
MySQL
```

Database sessions must be:

- Properly scoped.
- Properly closed.
- Safe for concurrent requests.
- Configurable through environment variables.

Do not create a new database engine for every request.

## 18. Migration Foundation

Initialize Alembic.

Create:

```
migrations/
```

The migration system should be able to:

```
Create Migration
       |
       v
Apply Migration
       |
       v
Update Database
```

Do not create the complete production schema in Phase 01.

That belongs to Phase 02.

## 19. Frontend Foundation

Create the initial frontend structure:

```
frontend/
|
+-- index.html
|
+-- css/
|   +-- style.css
|
+-- js/
    +-- app.js
```

The frontend should:

- Load successfully.
- Have a professional security-product foundation.
- Be responsive.
- Avoid unnecessary frameworks.
- Keep JavaScript modular.
- Keep styling separate from HTML.

## 20. Initial UI

The initial screen should communicate the product identity.

Suggested structure:

```
+--------------------------------+
| Web Security Auditor           |
+--------------------------------+
|                                |
| Secure Web Configuration       |
| Analysis Platform              |
|                                |
| [ Get Started ]                |
|                                |
+--------------------------------+
```

This is only a foundation.

The complete dashboard belongs to Phase 07.

## 21. Frontend API Configuration

Do not hard-code production API URLs throughout JavaScript.

Use a centralized configuration approach.

Example concept:

```
frontend
   |
   v
API Base URL
   |
   v
/api/v1
```

The final deployment should support same-origin API
communication where appropriate.

## 22. CORS Foundation

Configure CORS through environment-based settings.

Development may allow configured development origins.

Production must use an explicit allowlist.

Never use unrestricted production configuration such as:

```
allow_origins = ["*"]
```

when credentials or authenticated requests require
restricted origins.

## 23. Security Headers Foundation

The backend should have a structure for security middleware.

Future security controls may include:

```
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
Strict-Transport-Security
```

Do not claim that all production security headers are
complete in Phase 01.

Production hardening belongs to Phase 09/10.

## 24. Error Handling Foundation

Create a consistent error-handling approach.

The API should eventually return structured errors.

Concept:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "request_id": "..."
  }
}
```

Do not expose:

- Stack traces
- SQL queries
- Environment variables
- Internal filesystem paths
- Secrets

Development logging may contain more technical information,
but API responses must remain safe.

## 25. Request ID Foundation

Create a request ID mechanism.

Every API request should be traceable using a request ID.

Concept:

```
Client Request
      |
      v
Request ID
      |
      +----> Logs
      |
      +----> API Response
```

This becomes important for debugging and security auditing.

## 26. Logging Foundation

Create centralized logging configuration.

Logging should support:

- Timestamp
- Log level
- Module
- Message
- Request ID where available

Example levels:

```
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Do not log:

- Passwords
- API keys
- Session secrets
- Database credentials
- Sensitive authentication tokens

## 27. Testing Foundation

Create:

```
tests/
```

Initial tests should verify that:

- Application imports successfully.
- FastAPI application starts.
- Health endpoint works.
- Readiness endpoint exists.
- Basic API routing works.
- Configuration loads correctly.
- Database configuration can be initialized safely.

Example structure:

```
tests/
|
+-- unit/
|
+-- integration/
|
+-- security/
|
+-- conftest.py
```

The full test suite belongs to later phases.

## 28. Basic Health Test

Create a test for:

```
GET /api/v1/health
```

Expected behavior:

```
HTTP 200
```

The response must follow the API specification.

## 29. Application Startup Test

Verify that the application can start without errors.

Example:

```
Import Application
       |
       v
Create FastAPI App
       |
       v
Register Routes
       |
       v
Startup Successful
```

Startup must not require a live AI provider.

## 30. Security Requirements

Phase 01 must already follow the project's security-first
principles.

**Required**

- No hard-coded secrets.
- No unrestricted CORS in production.
- No debug information in production responses.
- No credentials in Git.
- No arbitrary filesystem access through API input.
- No user-controlled URL scanning.
- No scanner network requests.
- No AI-generated security decisions.

The scanner itself does not exist yet, so target validation
will be implemented in Phase 03.

## 31. What Must NOT Be Implemented

Do not implement these as actual features in Phase 01:

**Scanner**
- TLS scanning
- HTTP scanning
- Cookie scanning
- Header analysis
- Redirect analysis

**Security Engine**
- Finding generation
- Severity calculation
- Risk scoring

**AI**
- AI prompts
- AI provider calls
- AI summaries

**Advanced Features**
- Continuous monitoring
- Alerts
- Compliance mapping
- Multi-tenancy
- CI/CD integration
- Enterprise SSO

These belong to later phases.

## 32. Code Quality Requirements

Code must follow:

- Clear naming.
- Small functions.
- Separation of concerns.
- Type hints where appropriate.
- Explicit error handling.
- No unnecessary global state.
- No duplicated configuration logic.
- No hidden side effects.

Avoid:

- God classes
- God functions
- Circular imports
- Hard-coded credentials
- Magic configuration values
- Dead code
- Unused dependencies

## 33. Documentation Requirements

Update:

```
README.md
```

with:

- Project name
- Project purpose
- Technology stack
- Local setup
- Environment configuration
- Application startup
- Test command
- Documentation references

Do not duplicate the complete contents of `Docs/`.

The README should act as the project entry point.

## 34. Local Run Requirements

The application should support a simple development flow.

Concept:

```
Clone
  |
  v
Create Environment
  |
  v
Install Dependencies
  |
  v
Configure Environment
  |
  v
Start Application
  |
  v
Open Frontend
```

Backend example:

```
uvicorn app.main:app --reload
```

The exact command may be adjusted to match the final
application structure.

## 35. Verification Commands

After implementation, verify:

```
python --version
```

Then:

```
pytest
```

Then start the backend:

```
uvicorn app.main:app --reload
```

Verify:

```
GET /api/v1/health
```

and:

```
GET /api/v1/health/ready
```

The application must start without unexpected errors.

## 36. Acceptance Criteria

Phase 01 is accepted only if:

**Project**
- [ ] Project structure exists.
- [ ] Backend structure exists.
- [ ] Frontend structure exists.
- [ ] Tests structure exists.
- [ ] Documentation structure is preserved.

**Backend**
- [ ] FastAPI application starts.
- [ ] API versioning exists.
- [ ] Health endpoint works.
- [ ] Readiness endpoint exists.
- [ ] Error handling foundation exists.
- [ ] Logging foundation exists.
- [ ] Request ID foundation exists.

**Configuration**
- [ ] Environment-based configuration works.
- [ ] .env.example exists.
- [ ] Secrets are not hard-coded.
- [ ] .env is ignored by Git.

**Database**
- [ ] SQLAlchemy foundation exists.
- [ ] MySQL configuration exists.
- [ ] Alembic is initialized.
- [ ] Database session management exists.

**Frontend**
- [ ] Frontend loads.
- [ ] CSS loads.
- [ ] JavaScript loads.
- [ ] API base configuration exists.
- [ ] Initial UI is responsive.

**Testing**
- [ ] pytest runs.
- [ ] Health endpoint test passes.
- [ ] Application startup test passes.

## 37. Definition of Done

Phase 01 is officially complete when:

```
Foundation
    |
    v
Application Starts
    |
    v
API Works
    |
    v
Frontend Loads
    |
    v
Configuration Works
    |
    v
Database Layer Ready
    |
    v
Tests Pass
    |
    v
Security Baseline Verified
    |
    v
PHASE 01 COMPLETE
```

## 38. Expected Deliverables

At the end of this phase, the repository should contain:

```
app/
frontend/
tests/
migrations/

.env.example
.gitignore
requirements.txt
README.md
```

along with the existing:

```
Docs/
Phases/
```

directories.

## 39. Phase Output

The output of Phase 01 is not a complete security auditor.

It is a stable foundation capable of supporting the
following phases.

Expected result:

```
FastAPI
   |
   +-- API Foundation
   |
   +-- Configuration
   |
   +-- Database Layer
   |
   +-- Logging
   |
   +-- Error Handling
   |
   +-- Testing
   |
   v
Ready for Phase 02
```

## 40. AI Coding Agent Instructions

Use the following prompt when assigning Phase 01 to an
AI coding agent.

### Implementation Prompt

```
You are implementing Phase 01 — Foundation & Project Setup
of the AI-Powered Web Security Configuration Auditor.

First inspect the existing repository and all relevant files
inside:

Docs/
Phases/

Read and follow:

Docs/SRS.md
Docs/ARCHITECTURE.md
Docs/SECURITY.md
Docs/API.md
Docs/DATABASE.md
Docs/TESTING.md
Docs/DEPLOYMENT.md
Docs/UI_UX.md
Docs/AI_MODEL.md
Docs/SCANNER_SPECIFICATION.md
Docs/DEMO.md
Docs/ROADMAP.md
Phases/PHASE_01_FOUNDATION.md
```

### Your job

```
Implement ONLY Phase 01.

Create a clean and scalable project foundation containing:

FastAPI application foundation.
/api/v1 API structure.
Health endpoint.
Readiness endpoint.
Centralized configuration.
Environment variable support.
.env.example.
Secure .gitignore.
SQLAlchemy database foundation.
MySQL configuration.
Alembic migration foundation.
Frontend foundation using HTML/CSS/Vanilla JS.
Centralized frontend API configuration.
Logging foundation.
Request ID foundation.
Safe API error handling.
pytest testing foundation.
Basic startup and health tests.
README setup instructions.
```

### Critical restrictions

```
Do NOT implement:

TLS scanner
HTTP scanner
Cookie scanner
Security header scanner
Finding engine
Risk engine
AI provider integration
AI prompts
Continuous monitoring
Alerts
Multi-tenancy
Enterprise authentication
CI/CD security scanning

Those belong to later phases.
```

### Architecture rules

```
Maintain clear separation between:

API
Services
Database
Models
Schemas
Scanners
Core
Repositories

Do not place business logic in app/main.py.

Do not introduce unnecessary frameworks or dependencies.
```

### Security rules

```
Never:

Hard-code secrets.
Commit credentials.
Allow unrestricted production CORS.
Expose stack traces through API responses.
Log passwords or secrets.
Add arbitrary network requests.
Add target URL scanning.
Bypass documented security controls.
```

### Existing code protection

```
Before modifying anything:

Inspect the repository.
Understand the existing structure.
Reuse existing working code where appropriate.
Do not delete working functionality.
Do not rewrite unrelated modules.
Do not change documented contracts without justification.

If an existing implementation conflicts with Phase 01,
make the smallest safe change required.
```

### Testing

```
After implementation:

Run all existing tests.
Run new Phase 01 tests.
Start the FastAPI application.
Verify /api/v1/health.
Verify /api/v1/health/ready.
Verify frontend loading.
Verify configuration loading.
Verify database initialization.

Fix all errors introduced by your changes.

Do not hide failures by weakening tests.
```

### Final response

```
After implementation, provide:

Files created.
Files modified.
Dependencies added.
Database changes.
Tests executed.
Test results.
Security checks performed.
Any remaining issues.
Confirmation that Phase 01 is ready for Phase 02.

Do not claim completion if tests or startup are failing.
```

## 41. Phase Completion Report

After the coding agent finishes, record:

```
Phase:
01 — Foundation & Project Setup

Status:
[ ] Not Started
[ ] In Progress
[ ] Blocked
[ ] Complete

Implementation:
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

## 42. Transition to Phase 02

Only begin Phase 02 after all Phase 01 acceptance criteria
are satisfied.

Phase 02 will implement:

```
Database Models
       |
       v
Relationships
       |
       v
Repositories
       |
       v
Migrations
       |
       v
Persistent Scan Data Foundation
```

Phase 01 provides the foundation.

Phase 02 provides the persistent data layer.

## 43. Final Principle

The purpose of Phase 01 is not to make the product look
complete.

The purpose is to make the architecture strong enough that
future security functionality can be implemented safely.

Build the foundation first. Security features come next.