"""
Health and readiness route handlers.
GET /api/v1/health  — liveness (is the process alive?)
GET /api/v1/health/ready — readiness (are dependencies available?)
"""

import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.db.session import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Liveness check",
    description="Returns HTTP 200 when the API process is alive.",
    status_code=status.HTTP_200_OK,
)
async def health(request: Request) -> JSONResponse:
    """Confirm the application process is running."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": {"status": "healthy"},
        },
    )


@router.get(
    "/ready",
    summary="Readiness check",
    description="Returns HTTP 200 when required dependencies are reachable.",
    status_code=status.HTTP_200_OK,
)
async def ready(request: Request) -> JSONResponse:
    """
    Check whether the application's required dependencies are ready.
    Phase 01: database connectivity is attempted; AI is always 'disabled'.
    """
    db_ok = check_db_connection()
    db_status = "healthy" if db_ok else "unavailable"

    overall_ready = db_ok
    http_status = status.HTTP_200_OK if overall_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "success": overall_ready,
            "data": {
                "status": "ready" if overall_ready else "not_ready",
                "database": db_status,
                "ai": "disabled",  # Phase 08
            },
        },
    )
