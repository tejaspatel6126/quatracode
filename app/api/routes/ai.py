"""
Phase 08 — AI Explanation route.

GET /api/v1/scans/{scan_id}/ai-summary

Returns AI-generated explanation of deterministic scan results.

Security:
  - Ownership enforced (same as other scan routes)
  - AI_API_KEY is NEVER returned to the frontend
  - AI output is validated before return
  - Fallback to deterministic text if AI is unavailable
  - No modification of scan status, findings, or risk score
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.service import AIService
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.finding import Finding as DBFinding
from app.models.scan import Scan, SCAN_STATUS_COMPLETED
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI"])

_ai_service = AIService()


@router.get("/scans/{scan_id}/ai-summary")
async def get_ai_summary(
    scan_id: str,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    """
    Return AI-generated explanation of a completed scan.

    The deterministic scan results and risk scores are NOT modified.
    The AI only explains what the scanner found.

    If AI is disabled or fails, returns a deterministic fallback
    with ai_status=FALLBACK — the response always succeeds.
    """
    # ── Ownership check ──────────────────────────────────────────────────────
    scan = db.execute(
        select(Scan).where(Scan.scan_uuid == scan_id)
    ).scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if scan.status != SCAN_STATUS_COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="AI summary is only available for completed scans.",
        )

    # ── Load findings from DB ────────────────────────────────────────────────
    db_findings = db.execute(
        select(DBFinding)
        .where(DBFinding.scan_id == scan.id)
        .order_by(DBFinding.severity)
    ).scalars().all()

    findings_for_ai = [
        {
            "finding_id":   f.finding_code,
            "finding_code": f.finding_code,
            "title":        f.title,
            "severity":     f.severity,
            "category":     (f.category or "").upper(),
            "description":  f.description,
            "remediation":  f.recommendation or "",
            "evidence":     _extract_evidence(f.evidence),
        }
        for f in db_findings
    ]

    # ── Call AI service ──────────────────────────────────────────────────────
    try:
        summary = await _ai_service.explain_scan(
            scan_id    = scan_id,
            hostname   = scan.target_hostname or "",
            scheme     = "https",   # conservative default
            risk_score = float(scan.security_score or 0),
            risk_level = scan.risk_level or "UNKNOWN",
            findings   = findings_for_ai,
        )
    except Exception as exc:
        logger.exception("AI service raised unexpectedly for scan=%s: %s", scan_id, exc)
        # Should never reach here because AIService always falls back,
        # but handle defensively.
        raise HTTPException(
            status_code=503,
            detail="AI explanation is temporarily unavailable.",
        )

    # ── Serialize ────────────────────────────────────────────────────────────
    finding_explanations_out = [
        {
            "finding_code":      fe.finding_code,
            "summary":           fe.summary,
            "why_it_matters":    fe.why_it_matters,
            "impact":            fe.impact,
            "recommendation":    fe.recommendation,
            "owner_explanation": fe.owner_explanation,
            "ai_status":         fe.ai_status.value,
        }
        for fe in summary.finding_explanations
    ]

    return {
        "success": True,
        "data": {
            "scan_id":             scan_id,
            "ai_status":           summary.ai_status.value,
            "prompt_version":      summary.prompt_version,
            "executive_summary":   summary.executive_summary,
            "technical_summary":   summary.technical_summary,
            "top_priorities":      summary.top_priorities,
            "finding_explanations": finding_explanations_out,
            # These are deterministic values — AI cannot change them
            "risk_score":  float(scan.security_score or 0),
            "risk_level":  scan.risk_level or "UNKNOWN",
        },
    }


def _extract_evidence(evidence_json) -> list[dict]:
    """Extract evidence items from DB JSON field."""
    if not isinstance(evidence_json, dict):
        return []
    return evidence_json.get("items", [])
