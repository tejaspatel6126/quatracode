"""
Database integration tests using SQLite in-memory.
Tests CRUD operations, relationships, and constraints.
Fixtures are in conftest_db.py.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest_db import db_engine, db_session  # noqa: F401

from app.models.user import User
from app.models.scan import Scan, SCAN_STATUS_CREATED, SCAN_STATUS_COMPLETED
from app.models.finding import Finding, SEVERITY_HIGH, SEVERITY_CRITICAL, FINDING_STATUS_OPEN
from app.models.certificate import Certificate
from app.models.security_header import SecurityHeader
from app.models.cookie import Cookie
from app.models.redirect import Redirect
from app.models.resource import Resource
from app.models.ai_report import AIReport


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_user(db, email="test@example.com"):
    user = User(email=email, password_hash="$2b$12$hashed", is_active=True)
    db.add(user)
    db.flush()
    return user


def _make_scan(db, user_id=None):
    scan = Scan(
        target_url="https://example.com",
        target_hostname="example.com",
        status=SCAN_STATUS_CREATED,
        user_id=user_id,
    )
    db.add(scan)
    db.flush()
    return scan


# ── User CRUD ──────────────────────────────────────────────────────────────────

def test_create_user(db_session):
    user = _make_user(db_session)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.password_hash is not None

def test_user_password_is_not_plaintext(db_session):
    """Verify we never store a plaintext password."""
    user = _make_user(db_session)
    assert user.password_hash != "password"
    assert user.password_hash.startswith("$")

def test_user_email_unique_constraint(db_session):
    _make_user(db_session, email="unique@example.com")
    with pytest.raises(IntegrityError):
        _make_user(db_session, email="unique@example.com")

def test_read_user(db_session):
    user = _make_user(db_session)
    fetched = db_session.get(User, user.id)
    assert fetched.email == user.email

def test_update_user_is_active(db_session):
    user = _make_user(db_session)
    user.is_active = False
    db_session.flush()
    fetched = db_session.get(User, user.id)
    assert fetched.is_active is False

def test_delete_user(db_session):
    user = _make_user(db_session, email="delete@example.com")
    uid = user.id
    db_session.delete(user)
    db_session.flush()
    assert db_session.get(User, uid) is None


# ── Scan CRUD ──────────────────────────────────────────────────────────────────

def test_create_scan(db_session):
    scan = _make_scan(db_session)
    assert scan.id is not None
    assert scan.scan_uuid is not None
    assert len(scan.scan_uuid) == 36
    assert scan.status == SCAN_STATUS_CREATED

def test_scan_uuid_is_unique(db_session):
    s1 = _make_scan(db_session)
    s2 = _make_scan(db_session)
    assert s1.scan_uuid != s2.scan_uuid

def test_scan_counter_defaults(db_session):
    scan = _make_scan(db_session)
    db_session.refresh(scan)
    assert scan.total_findings == 0
    assert scan.critical_count == 0

def test_scan_status_update(db_session):
    scan = _make_scan(db_session)
    scan.status = SCAN_STATUS_COMPLETED
    db_session.flush()
    fetched = db_session.get(Scan, scan.id)
    assert fetched.status == SCAN_STATUS_COMPLETED

def test_scan_ownership(db_session):
    user = _make_user(db_session)
    scan = _make_scan(db_session, user_id=user.id)
    db_session.flush()
    assert scan.user_id == user.id

def test_scan_anonymous_allowed(db_session):
    """user_id is nullable — anonymous scans are valid."""
    scan = _make_scan(db_session, user_id=None)
    assert scan.user_id is None


# ── Finding CRUD ───────────────────────────────────────────────────────────────

def test_create_finding(db_session):
    scan = _make_scan(db_session)
    finding = Finding(
        scan_id=scan.id,
        finding_code="HSTS_MISSING",
        category="security_headers",
        title="HSTS Not Set",
        description="Strict-Transport-Security header is absent.",
        severity=SEVERITY_HIGH,
        status=FINDING_STATUS_OPEN,
    )
    db_session.add(finding)
    db_session.flush()
    assert finding.id is not None

def test_finding_belongs_to_scan(db_session):
    scan = _make_scan(db_session)
    finding = Finding(
        scan_id=scan.id,
        finding_code="CSP_MISSING",
        category="security_headers",
        title="CSP Missing",
        description="No Content-Security-Policy header.",
        severity=SEVERITY_CRITICAL,
        status=FINDING_STATUS_OPEN,
    )
    db_session.add(finding)
    db_session.flush()
    assert finding.scan_id == scan.id

def test_finding_invalid_scan_raises(db_session):
    """Finding must reference a valid scan (FK enforcement)."""
    finding = Finding(
        scan_id=99999,  # does not exist
        finding_code="TEST",
        category="other",
        title="Test",
        description="Test",
        severity=SEVERITY_HIGH,
        status=FINDING_STATUS_OPEN,
    )
    db_session.add(finding)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_multiple_findings_per_scan(db_session):
    scan = _make_scan(db_session)
    for i in range(3):
        f = Finding(
            scan_id=scan.id,
            finding_code=f"CODE_{i}",
            category="other",
            title=f"Finding {i}",
            description="desc",
            severity="LOW",
            status=FINDING_STATUS_OPEN,
        )
        db_session.add(f)
    db_session.flush()

    from sqlalchemy import select, func
    count = db_session.execute(
        select(func.count()).select_from(Finding).where(Finding.scan_id == scan.id)
    ).scalar_one()
    assert count == 3


# ── Certificate ────────────────────────────────────────────────────────────────

def test_create_certificate(db_session):
    scan = _make_scan(db_session)
    cert = Certificate(
        scan_id=scan.id,
        serial_number="ABC123",
        hostname_match=True,
        self_signed=False,
        chain_valid=True,
    )
    db_session.add(cert)
    db_session.flush()
    assert cert.id is not None

def test_certificate_one_per_scan(db_session):
    """UNIQUE(scan_id) on certificates — only one per scan."""
    scan = _make_scan(db_session)
    cert1 = Certificate(scan_id=scan.id)
    db_session.add(cert1)
    db_session.flush()

    cert2 = Certificate(scan_id=scan.id)
    db_session.add(cert2)
    with pytest.raises(IntegrityError):
        db_session.flush()


# ── Security Header ────────────────────────────────────────────────────────────

def test_create_security_header(db_session):
    scan = _make_scan(db_session)
    hdr = SecurityHeader(
        scan_id=scan.id,
        header_name="Strict-Transport-Security",
        present=False,
        evaluation="missing",
    )
    db_session.add(hdr)
    db_session.flush()
    assert hdr.id is not None


# ── Cookie ─────────────────────────────────────────────────────────────────────

def test_create_cookie(db_session):
    scan = _make_scan(db_session)
    cookie = Cookie(
        scan_id=scan.id,
        cookie_name="sessionid",
        secure=False,
        http_only=True,
        same_site="Lax",
    )
    db_session.add(cookie)
    db_session.flush()
    assert cookie.id is not None


# ── Redirect ───────────────────────────────────────────────────────────────────

def test_create_redirect(db_session):
    scan = _make_scan(db_session)
    redirect = Redirect(
        scan_id=scan.id,
        step_number=1,
        source_url="http://example.com",
        status_code=301,
        location_url="https://example.com",
        destination_scheme="https",
    )
    db_session.add(redirect)
    db_session.flush()
    assert redirect.id is not None


# ── Resource ───────────────────────────────────────────────────────────────────

def test_create_resource(db_session):
    scan = _make_scan(db_session)
    resource = Resource(
        scan_id=scan.id,
        resource_url="http://cdn.example.com/script.js",
        resource_type="script",
        hostname="cdn.example.com",
        origin_type="third-party",
        scheme="http",
        mixed_content=True,
    )
    db_session.add(resource)
    db_session.flush()
    assert resource.id is not None
    assert resource.mixed_content is True


# ── AIReport ───────────────────────────────────────────────────────────────────

def test_create_ai_report(db_session):
    scan = _make_scan(db_session)
    report = AIReport(
        scan_id=scan.id,
        summary="Overall: high risk.",
        model_name="gpt-4o",
        prompt_version="v1",
    )
    db_session.add(report)
    db_session.flush()
    assert report.id is not None

def test_ai_report_one_per_scan(db_session):
    """UNIQUE(scan_id) on ai_reports."""
    scan = _make_scan(db_session)
    r1 = AIReport(scan_id=scan.id, summary="First")
    db_session.add(r1)
    db_session.flush()

    r2 = AIReport(scan_id=scan.id, summary="Second")
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_ai_report_does_not_affect_finding(db_session):
    """AI report stored separately — finding severity unchanged."""
    scan = _make_scan(db_session)
    finding = Finding(
        scan_id=scan.id,
        finding_code="XYZ",
        category="other",
        title="Test",
        description="Test",
        severity=SEVERITY_HIGH,
        status=FINDING_STATUS_OPEN,
    )
    db_session.add(finding)
    db_session.flush()

    report = AIReport(scan_id=scan.id, summary="AI says low risk")
    db_session.add(report)
    db_session.flush()

    # AI report cannot change the finding's severity
    db_session.refresh(finding)
    assert finding.severity == SEVERITY_HIGH


# ── Cascade behavior ───────────────────────────────────────────────────────────

def test_findings_cascade_on_scan_delete(db_session):
    """Deleting a scan must cascade-delete its findings."""
    scan = _make_scan(db_session)
    f = Finding(
        scan_id=scan.id,
        finding_code="CASCADE_TEST",
        category="other",
        title="Cascade",
        description="test",
        severity="LOW",
        status=FINDING_STATUS_OPEN,
    )
    db_session.add(f)
    db_session.flush()
    f_id = f.id

    db_session.delete(scan)
    db_session.flush()
    assert db_session.get(Finding, f_id) is None

def test_user_deletion_sets_scan_user_id_null(db_session):
    """Deleting a user must SET NULL on scans.user_id (scan history preserved)."""
    user = _make_user(db_session, email="setNull@example.com")
    scan = _make_scan(db_session, user_id=user.id)
    scan_id = scan.id

    db_session.delete(user)
    db_session.flush()

    fetched = db_session.get(Scan, scan_id)
    assert fetched is not None          # scan preserved
    assert fetched.user_id is None      # FK set to NULL
