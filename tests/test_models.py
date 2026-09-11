"""
Model unit tests — verify ORM model structure, defaults, and repr.
These tests do NOT require MySQL.
"""

import pytest

from app.models.user import User
from app.models.scan import Scan, SCAN_STATUSES, SCAN_STATUS_CREATED
from app.models.finding import Finding, SEVERITIES, SEVERITY_HIGH, FINDING_STATUS_OPEN
from app.models.certificate import Certificate
from app.models.security_header import SecurityHeader
from app.models.cookie import Cookie
from app.models.redirect import Redirect
from app.models.resource import Resource
from app.models.ai_report import AIReport


# ── User ───────────────────────────────────────────────────────────────────────

def test_user_tablename():
    assert User.__tablename__ == "users"

def test_user_has_required_columns():
    cols = {c.name for c in User.__table__.columns}
    assert "id" in cols
    assert "email" in cols
    assert "password_hash" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

def test_user_email_is_unique():
    col = User.__table__.c["email"]
    assert col.unique is True or any(
        "email" in [c.name for c in idx.columns]
        and idx.unique
        for idx in User.__table__.indexes
    )

def test_user_password_hash_is_nullable():
    assert User.__table__.c["password_hash"].nullable is True


# ── Scan ───────────────────────────────────────────────────────────────────────

def test_scan_tablename():
    assert Scan.__tablename__ == "scans"

def test_scan_has_uuid_column():
    assert "scan_uuid" in {c.name for c in Scan.__table__.columns}

def test_scan_status_constants_complete():
    assert "created" in SCAN_STATUSES
    assert "completed" in SCAN_STATUSES
    assert "failed" in SCAN_STATUSES
    assert len(SCAN_STATUSES) == 9  # DATABASE.md §6.2

def test_scan_has_counters():
    cols = {c.name for c in Scan.__table__.columns}
    for counter in ("total_findings", "critical_count", "high_count",
                    "medium_count", "low_count", "info_count", "passed_count"):
        assert counter in cols, f"Missing counter column: {counter}"

def test_scan_user_id_is_nullable():
    assert Scan.__table__.c["user_id"].nullable is True


# ── Finding ────────────────────────────────────────────────────────────────────

def test_finding_tablename():
    assert Finding.__tablename__ == "findings"

def test_finding_severity_constants():
    assert SEVERITIES == {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "PASS"}

def test_finding_has_evidence_column():
    assert "evidence" in {c.name for c in Finding.__table__.columns}

def test_finding_evidence_is_nullable():
    assert Finding.__table__.c["evidence"].nullable is True

def test_finding_status_default():
    assert FINDING_STATUS_OPEN == "open"


# ── Certificate ────────────────────────────────────────────────────────────────

def test_certificate_tablename():
    assert Certificate.__tablename__ == "certificates"

def test_certificate_scan_id_unique():
    constraints = {c.name for c in Certificate.__table__.constraints}
    assert "uq_certificate_scan" in constraints

def test_certificate_has_json_columns():
    cols = {c.name for c in Certificate.__table__.columns}
    assert "san_entries" in cols
    assert "protocol_summary" in cols


# ── SecurityHeader ─────────────────────────────────────────────────────────────

def test_security_header_tablename():
    assert SecurityHeader.__tablename__ == "security_headers"

def test_security_header_present_default():
    col = SecurityHeader.__table__.c["present"]
    assert col.server_default is not None


# ── Cookie ─────────────────────────────────────────────────────────────────────

def test_cookie_tablename():
    assert Cookie.__tablename__ == "cookies"

def test_cookie_value_not_stored():
    """Cookie VALUES must not be stored — only security attributes."""
    col_names = {c.name for c in Cookie.__table__.columns}
    assert "cookie_value" not in col_names
    assert "value" not in col_names


# ── Redirect ───────────────────────────────────────────────────────────────────

def test_redirect_tablename():
    assert Redirect.__tablename__ == "redirects"

def test_redirect_has_step_number():
    assert "step_number" in {c.name for c in Redirect.__table__.columns}


# ── Resource ───────────────────────────────────────────────────────────────────

def test_resource_tablename():
    assert Resource.__tablename__ == "resources"

def test_resource_mixed_content_not_nullable():
    col = Resource.__table__.c["mixed_content"]
    assert col.nullable is False


# ── AIReport ───────────────────────────────────────────────────────────────────

def test_ai_report_tablename():
    assert AIReport.__tablename__ == "ai_reports"

def test_ai_report_scan_id_unique():
    constraints = {c.name for c in AIReport.__table__.constraints}
    assert "uq_ai_report_scan" in constraints

def test_ai_report_has_model_name():
    assert "model_name" in {c.name for c in AIReport.__table__.columns}
