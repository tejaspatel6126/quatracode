# AI-Powered Web Security Configuration Auditor

## Overview

Identifies publicly observable SSL/TLS and web security configuration weaknesses using deterministic security scanners and AI-powered explanations.

**Project Type:** Hackathon — AI & Cybersecurity  
**Problem Statement:** Problem 4.3 — Hidden SSL/TLS and Web Security Configuration Weaknesses

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | MySQL 8.x |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Testing | pytest, pytest-asyncio, HTTPX |

---

## Project Structure

```
quatracode/
├── app/
│   ├── main.py               # FastAPI application entry point
│   ├── api/routes/           # Route handlers
│   │   ├── __init__.py       # api_v1_router aggregator
│   │   └── health.py         # GET /api/v1/health, /api/v1/health/ready
│   ├── core/
│   │   ├── config.py         # Pydantic-Settings configuration
│   │   ├── logging.py        # Centralized logging
│   │   ├── security.py       # RequestID + SecurityHeaders middleware
│   │   └── exceptions.py     # Exception handlers, safe error responses
│   ├── db/
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   └── session.py        # Engine, SessionLocal, get_db dependency
│   ├── models/               # ORM models (Phase 02+)
│   ├── schemas/              # Pydantic schemas (Phase 02+)
│   ├── repositories/         # Data access layer (Phase 02+)
│   ├── services/             # Business services (Phase 02+)
│   └── scanners/             # Security scanners (Phase 04+)
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_config.py
│   └── test_security.py
├── migrations/               # Alembic migrations
├── Docs/                     # Project documentation
├── Phases/                   # Phase specifications
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Local Setup

### 1. Prerequisites

- Python 3.11+
- Git
- MySQL 8.x (optional for Phase 01 — readiness check will show unavailable)

### 2. Clone and enter the project

```bash
git clone <repo-url>
cd quatracode
```

### 3. Create virtual environment

```bash
python -m venv .venv
```

**Activate (Windows PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Activate (Linux/macOS):**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in DATABASE_URL, SECRET_KEY, etc.
```

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

Application: `http://localhost:8000`  
API docs (dev only): `http://localhost:8000/api/docs`  
Health check: `http://localhost:8000/api/v1/health`  
Readiness: `http://localhost:8000/api/v1/health/ready`

### 7. Run tests

```bash
pytest
```

---

## API Endpoints (Phase 01)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Liveness — is the process alive? |
| GET | `/api/v1/health/ready` | Readiness — are dependencies available? |

---

## Security Notes

- No secrets are hardcoded. All sensitive values come from `.env`.
- `.env` is excluded from Git via `.gitignore`.
- CORS is explicitly configured — no wildcard origins.
- API responses never expose tracebacks, database errors, or internal paths.
- All DOM updates use `textContent` (never `innerHTML` with untrusted data).
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) are applied on every response.

---

## Phase Status

| Phase | Status |
|---|---|
| 01 — Foundation & Project Setup | ✅ Complete |
| 02 — Database Models | ⏳ Pending |
| 03 — Target & Security Validation | ⏳ Pending |
| 04 — Scanner Engine | ⏳ Pending |
| 05 — Finding & Risk Engine | ⏳ Pending |
| 06 — API & Scan Manager | ⏳ Pending |
| 07 — Frontend Dashboard | ⏳ Pending |
| 08 — AI Integration | ⏳ Pending |
| 09 — Testing & Hardening | ⏳ Pending |
| 10 — Integration & Deployment | ⏳ Pending |
