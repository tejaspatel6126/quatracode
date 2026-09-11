"""
Phase 06 — Scan API routes.

POST   /api/v1/scans            — Create scan (validate + run synchronously for demo)
GET    /api/v1/scans            — List scans (paginated, ownership enforced)
GET    /api/v1/scans/{id}       — Get scan status
GET    /api/v1/scans/{id}/results — Full scan results + findings + risk
DELETE /api/v1/scans/{id}       — Cancel / delete scan

Security:
  - Ownership enforced on every scan access (user can only see their own)
  - Target validation via Phase 03 boundary (ValidatedTarget)
  - Scanner via Phase 04 CoreScanner
  - Findings + risk via Phase 05 engines
  - No user-controlled severity or risk
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.findings.engine import FindingEngine
from app.findings.risk_engine import RiskEngine
from app.models.scan import (
    Scan,
    SCAN_STATUS_COMPLETED,
    SCAN_STATUS_FAILED,
    SCAN_STATUS_QUEUED,
    SCAN_STATUS_SCANNING,
)
from app.models.user import User
from app.repositories.scan_repository import ScanRepository
from app.scanners.scanner import CoreScanner
from app.security.target_validator import TargetSecurityError, ValidatedTarget, validate_target

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scans", tags=["Scans"])

# Phase 04 scanner singleton (stateless)
_scanner        = CoreScanner()
# Phase 05 engines (stateless, safe to reuse)
_finding_engine = FindingEngine()
_risk_engine    = RiskEngine()


# ── Request schemas ───────────────────────────────────────────────────────────

class CreateScanRequest(BaseModel):
    target_url: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scan_dict(scan: Scan) -> dict:
    return {
        "scan_id":        scan.scan_uuid,
        "id":             scan.scan_uuid,
        "target_url":     scan.target_url,
        "target_hostname":scan.target_hostname,
        "status":         scan.status,
        "security_score": float(scan.security_score) if scan.security_score is not None else None,
        "risk_level":     scan.risk_level,
        "total_findings": scan.total_findings,
        "critical_count": scan.critical_count,
        "high_count":     scan.high_count,
        "medium_count":   scan.medium_count,
        "low_count":      scan.low_count,
        "info_count":     scan.info_count,
        "started_at":     scan.started_at.isoformat() if scan.started_at else None,
        "completed_at":   scan.completed_at.isoformat() if scan.completed_at else None,
        "created_at":     scan.created_at.isoformat() if scan.created_at else None,
    }


def _get_owned_scan(scan_uuid: str, user: User, db: Session) -> Scan:
    repo = ScanRepository(db)
    scan = repo.get_by_uuid(scan_uuid)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found.")
    if scan.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return scan


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── POST /scans ───────────────────────────────────────────────────────────────

@router.post("", status_code=202)
async def create_scan(
    body: CreateScanRequest,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    # 1. Phase 03 — target validation (SSRF boundary)
    try:
        validated = validate_target(body.target_url)
    except TargetSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid target: {exc}")

    # 2. Persist scan record
    repo = ScanRepository(db)
    scan = Scan(
        user_id          = user.id,
        target_url       = validated.normalized_url,
        target_hostname  = validated.hostname,
        status           = SCAN_STATUS_QUEUED,
        started_at       = _now(),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # 3. Run scan synchronously (demo mode — Phase 06 full async = future)
    scan.status = SCAN_STATUS_SCANNING
    db.commit()

    try:
        # CoreScanner.scan() is synchronous (blocking I/O via httpx).
        # Run it in a thread pool to avoid blocking the event loop.
        scan_result = await asyncio.to_thread(_scanner.scan, validated)
    except Exception as exc:
        logger.error("Scanner failed for %s: %s", validated.hostname, exc)
        scan.status = SCAN_STATUS_FAILED
        scan.completed_at = _now()
        db.commit()
        return {"success": True, "data": {"scan_id": scan.scan_uuid, "status": scan.status}}

    # 4. Phase 05 — findings + risk
    findings   = _finding_engine.run(scan_result)
    risk       = _risk_engine.calculate(findings)

    # 5. Update scan record with results
    scan.status         = SCAN_STATUS_COMPLETED
    scan.completed_at   = _now()
    scan.security_score = risk.score
    scan.risk_level     = risk.risk_level.value
    scan.total_findings = len(findings)
    counts = risk.severity_counts
    scan.critical_count = counts.get("CRITICAL", 0)
    scan.high_count     = counts.get("HIGH",     0)
    scan.medium_count   = counts.get("MEDIUM",   0)
    scan.low_count      = counts.get("LOW",      0)
    scan.info_count     = counts.get("INFO",     0)

    # Persist findings to DB
    from app.models.finding import Finding
    for f in findings:
        db_finding = Finding(
            scan_id        = scan.id,
            finding_code   = f.finding_id,
            category       = f.category.value.lower(),
            severity       = f.severity.value,
            title          = f.title,
            description    = f.description,
            recommendation = f.remediation,
            evidence       = {"items": [{"observed": e.observed, "detail": e.detail} for e in f.evidence]},
        )
        db.add(db_finding)

    db.commit()
    db.refresh(scan)

    logger.info("Scan completed: uuid=%s host=%s score=%.1f",
                scan.scan_uuid, scan.target_hostname, risk.score)

    # Store raw scan result in memory for this request's /results call
    _scan_result_cache[scan.scan_uuid] = (scan_result, findings, risk)

    return {"success": True, "data": {"scan_id": scan.scan_uuid, "status": scan.status}}


# Simple in-process cache for results (Phase 06 full = Redis/DB blob)
_scan_result_cache: dict = {}


# ── GET /scans ────────────────────────────────────────────────────────────────

@router.get("")
def list_scans(
    page:     int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    repo   = ScanRepository(db)
    offset = (page - 1) * per_page
    scans  = repo.list_by_user(user.id, limit=per_page, offset=offset)

    # Total count
    total = db.execute(
        select(func.count()).select_from(Scan).where(Scan.user_id == user.id)
    ).scalar_one()

    # Summary counts for dashboard stats
    from app.models.scan import SCAN_STATUS_COMPLETED, SCAN_STATUS_FAILED
    completed = db.execute(
        select(func.count()).select_from(Scan)
        .where(Scan.user_id == user.id, Scan.status == SCAN_STATUS_COMPLETED)
    ).scalar_one()
    failed = db.execute(
        select(func.count()).select_from(Scan)
        .where(Scan.user_id == user.id, Scan.status == SCAN_STATUS_FAILED)
    ).scalar_one()
    running = total - completed - failed

    return {
        "success": True,
        "data": {
            "scans": [_scan_dict(s) for s in scans],
            "meta": {
                "total":       total,
                "page":        page,
                "per_page":    per_page,
                "total_pages": max(1, -(-total // per_page)),
                "completed":   completed,
                "failed":      failed,
                "running":     max(0, running),
            },
        },
    }


# ── GET /scans/{id} ───────────────────────────────────────────────────────────

@router.get("/{scan_id}")
def get_scan(
    scan_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    scan = _get_owned_scan(scan_id, user, db)
    return {"success": True, "data": {"scan": _scan_dict(scan)}}


# ── GET /scans/{id}/results ───────────────────────────────────────────────────

@router.get("/{scan_id}/results")
def get_scan_results(
    scan_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    scan = _get_owned_scan(scan_id, user, db)

    if scan.status != SCAN_STATUS_COMPLETED:
        return {"success": True, "data": {"scan": _scan_dict(scan), "findings": [], "risk": {}}}

    # Load findings from DB
    from app.models.finding import Finding as DBFinding
    db_findings = db.execute(
        select(DBFinding)
        .where(DBFinding.scan_id == scan.id)
        .order_by(DBFinding.severity)
    ).scalars().all()

    findings_out = []
    for f in db_findings:
        evidence = []
        if isinstance(f.evidence, dict):
            for item in f.evidence.get("items", []):
                evidence.append({"observed": item.get("observed", ""), "detail": item.get("detail")})
        findings_out.append({
            "finding_id":  f.finding_code,
            "check_id":    f.finding_code,
            "category":    (f.category or "").upper(),
            "title":       f.title,
            "description": f.description,
            "severity":    f.severity,
            "evidence":    evidence,
            "remediation": f.recommendation or "",
            "references":  [],
        })

    # Risk summary from scan record
    risk_out = {
        "score":      float(scan.security_score) if scan.security_score else 0.0,
        "risk_level": scan.risk_level or "VERY_LOW",
        "severity_counts": {
            "CRITICAL": scan.critical_count,
            "HIGH":     scan.high_count,
            "MEDIUM":   scan.medium_count,
            "LOW":      scan.low_count,
            "INFO":     scan.info_count,
        },
    }

    # Raw observations from in-memory cache (present if same process)
    raw = {}
    if scan_id in _scan_result_cache:
        scan_result, _, _ = _scan_result_cache[scan_id]
        raw = _serialise_raw(scan_result)

    return {
        "success": True,
        "data": {
            "scan":             _scan_dict(scan),
            "findings":         findings_out,
            "risk":             risk_out,
            "raw_observations": raw,
        },
    }


# ── DELETE /scans/{id} ────────────────────────────────────────────────────────

@router.delete("/{scan_id}", status_code=200)
def cancel_scan(
    scan_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    scan = _get_owned_scan(scan_id, user, db)
    from app.models.scan import SCAN_STATUS_FAILED
    if scan.status not in (SCAN_STATUS_COMPLETED, SCAN_STATUS_FAILED):
        scan.status = "failed"
        scan.completed_at = _now()
        db.commit()
    return {"success": True, "data": {"message": "Scan cancelled."}}


# ── Serialise raw ScanResult to dict ─────────────────────────────────────────

def _serialise_raw(sr) -> dict:
    """Convert Phase 04 ScanResult to a safe JSON-serialisable dict."""
    out: dict = {}

    if sr.tls:
        out["tls"] = {
            "available":    sr.tls.available,
            "version":      sr.tls.version,
            "tls_1_0":      sr.tls.tls_1_0,
            "tls_1_1":      sr.tls.tls_1_1,
            "tls_1_2":      sr.tls.tls_1_2,
            "tls_1_3":      sr.tls.tls_1_3,
            "cipher_suite": sr.tls.cipher_suite,
        }

    if sr.certificate:
        c = sr.certificate
        out["certificate"] = {
            "available":           c.available,
            "subject":             c.subject,
            "issuer":              c.issuer,
            "not_before":          c.not_before.isoformat() if c.not_before else None,
            "not_after":           c.not_after.isoformat()  if c.not_after  else None,
            "days_until_expiry":   c.days_until_expiry,
            "hostname_validation": str(c.hostname_validation) if c.hostname_validation else None,
            "is_self_signed":      c.is_self_signed,
            "san_domains":         c.san_domains or [],
        }

    if sr.headers:
        h = sr.headers
        out["headers"] = {
            "available":             h.available,
            "hsts":                  {"present": h.hsts.present, "max_age": h.hsts.max_age},
            "csp":                   {"present": h.csp.present,  "raw_value": h.csp.raw_value},
            "x_content_type_options":{"present": h.x_content_type_options.present},
            "frame_protection":      {
                "x_frame_options_present":    h.frame_protection.x_frame_options_present,
                "csp_frame_ancestors_present":h.frame_protection.csp_frame_ancestors_present,
            },
            "referrer_policy":       {"present": h.referrer_policy.present, "normalized_value": h.referrer_policy.normalized_value},
            "permissions_policy":    {"present": h.permissions_policy.present},
        }

    if sr.cookies:
        out["cookies"] = {
            "available": sr.cookies.available,
            "cookies":   [
                {
                    "name":      c.name,
                    "secure":    c.secure,
                    "http_only": c.http_only,
                    "same_site": c.same_site,
                }
                for c in (sr.cookies.cookies or [])
            ],
        }

    if sr.redirects:
        r = sr.redirects
        out["redirects"] = {
            "available":               r.available,
            "https_redirect_observed": r.https_redirect_observed,
            "redirect_count":          r.redirect_count,
            "final_url":               r.final_url,
        }

    if hasattr(sr, 'network') and sr.network:
        n = sr.network
        out["network"] = {
            "available":    n.available,
            "nmap_version": getattr(n, "nmap_version", None),
            "scanned_at":   n.scanned_at.isoformat() if getattr(n, "scanned_at", None) else None,
            "ports": [
                {
                    "port":         p.port,
                    "protocol":     p.protocol,
                    "state":        p.state,
                    "service_name": p.service_name,
                }
                for p in (n.ports or [])
            ],
        }

    return out
