"""
Phase 06 — Auth routes.
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/register
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger   = logging.getLogger(__name__)
settings = get_settings()
router   = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    str
    password: str


class RegisterRequest(BaseModel):
    email:    str
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_session(response: Response, user_id: int) -> None:
    token = create_session_token(user_id)
    response.set_cookie(
        key      = SESSION_COOKIE,
        value    = token,
        max_age  = SESSION_MAX_AGE,
        httponly = True,
        samesite = "lax",
        secure   = settings.is_production,
        path     = "/",
    )


def _user_dict(user: User) -> dict:
    return {"id": user.id, "email": user.email}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", summary="Sign in")
async def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email.lower().strip())

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    _set_session(response, user.id)
    logger.info("User login: id=%d email=%s", user.id, user.email)
    return {"success": True, "data": {"user": _user_dict(user)}}


@router.post("/logout", summary="Sign out")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"success": True, "data": {"message": "Signed out."}}


@router.get("/me", summary="Current user")
async def me(user: User = Depends(get_current_user)):
    return {"success": True, "data": {"user": _user_dict(user)}}


@router.post("/register", summary="Register new user", status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    repo  = UserRepository(db)
    email = body.email.lower().strip()

    if repo.get_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )

    user = User(email=email, password_hash=hash_password(body.password), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_session(response, user.id)
    logger.info("New user registered: id=%d email=%s", user.id, user.email)
    return {"success": True, "data": {"user": _user_dict(user)}}
