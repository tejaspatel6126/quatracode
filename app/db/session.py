"""
Database session and engine configuration.
Engine created once; sessions are per-request via dependency injection.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,       # validate connections before using from pool
    echo=False,               # never echo SQL — would expose query details in logs
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for use as a FastAPI dependency.
    Session is always closed when the request is done.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Lightweight connectivity check ────────────────────────────────────────────
def check_db_connection() -> bool:
    """
    Return True if a basic SELECT 1 succeeds, False otherwise.
    Used by the readiness endpoint.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # Log the fact of failure — NOT the credentials or connection string
        logger.warning("Database connectivity check failed: %s", type(exc).__name__)
        return False
