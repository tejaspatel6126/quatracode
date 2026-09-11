"""
API v1 router — aggregates all v1 route modules.
"""

from fastapi import APIRouter

from app.api.routes import ai, auth, health, scans

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(ai.router)
