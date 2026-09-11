"""
Phase 06 — Auth & session dependencies.

Uses itsdangerous signed cookies for session management.
Passwords hashed with bcrypt via passlib.
NO raw passwords, secrets, or hashes in API responses.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import bcrypt as _bcrypt_lib
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger   = logging.getLogger(__name__)
settings = get_settings()

# Session cookie name — HttpOnly, SameSite=Lax, Secure in production
SESSION_COOKIE  = "sa_session"
SESSION_MAX_AGE = 60 * 60 * 8   # 8 hours


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="sa-session")


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _bcrypt_lib.hashpw(plain.encode(), _bcrypt_lib.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt_lib.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── Session helpers ────────────────────────────────────────────────────────────

def create_session_token(user_id: int) -> str:
    return _serializer().dumps({"uid": user_id})


def decode_session_token(token: str) -> Optional[int]:
    try:
        data = _serializer().loads(token, max_age=SESSION_MAX_AGE)
        return int(data["uid"])
    except (SignatureExpired, BadSignature, KeyError, ValueError):
        return None


# ── FastAPI dependency: current user ──────────────────────────────────────────

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Resolve authenticated user from session cookie. Raises 401 if invalid."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required.")

    user_id = decode_session_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Session expired. Please sign in again.")

    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found or inactive.")
    return user


def optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising."""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None
