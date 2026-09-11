"""
FastAPI application entry point.
Assembles middleware, routers, and exception handlers.
No business logic lives here.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.security import RequestIDMiddleware, SecurityHeadersMiddleware

# ── Bootstrap logging first ───────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan (replaces deprecated on_event) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Application starting | env=%s | debug=%s",
        settings.APP_ENV,
        settings.DEBUG,
    )
    yield
    logger.info("Application shutting down")


# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "AI-Powered Web Security Configuration Auditor — "
        "identifies SSL/TLS and HTTP security configuration weaknesses."
    ),
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
    openapi_url="/api/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# ── Middleware (order matters — outermost runs first on request) ───────────────
# 1. Request ID (must be first so all later middleware can read request_id)
app.add_middleware(RequestIDMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS — configured from environment; never wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,   # credentials must be explicitly re-enabled later
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_v1_router)

# ── Static files (frontend) ───────────────────────────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
