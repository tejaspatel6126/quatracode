"""
Repository layer tests — CRUD, filtering, pagination, error wrapping.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest_db import db_engine, db_session  # noqa: F401

from app.repositories.user_repository import UserRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.ai_repository import AIReportRepository
from app.models.scan import SCAN_STATUS_CREATED, SCAN_STATUS_COMPLETED, SCAN_STATUS_FAILED
from app.models.finding import SEVERITY_HIGH, SEVERITY_CRITICAL, FINDING_STATUS_OPEN
from app.core.exceptions import NotFoundError


# ── Helpers ────────────────────────────────────────────────────────────────────

def _user_repo(db):
    return UserRepository(db)

def _scan_repo(db):
    return ScanRepository(db)

def _finding_repo(db):
    return FindingRepository(db)

def _ai_repo(db):
    return AIReportRepository(db)

def _create_user(repo, email="repo@example.com"):
    return repo.create(email=email, is_active=True, password_hash="$2b$hash")

def _create_scan(repo, user_id=None):
    return repo.create(
        target_url="https://repo-test.com",
        target_hostname="repo-test.com",
        status=SCAN_STATUS_CREATED,
        user_id=user_id,
    )


# ── UserRepository ─────────────────────────────────────────────────────────────

def test_user_repo_create(db_session):
    repo = _user_repo(db_session)
    user = _create_user(repo)
    assert user.id is not None

def test_user_repo_get(db_session):
    repo = _user_repo(db_session)
    user = _create_user(repo, email="get@example.com")
    fetched = repo.get(user.id)
    assert fetched.email == "get@example.com"

def test_user_repo_get_not_found(db_session):
    repo = _user_repo(db_session)
    with pytest.raises(NotFoundError):
        repo.get(999999)

def test_user_repo_get_by_email(db_session):
    repo = _user_repo(db_session)
    _create_user(repo, email="find@example.com")
    found = repo.get_by_email("find@example.com")
    assert found is not None
    assert found.email == "find@example.com"

def test_user_repo_get_by_email_missing(db_session):
    repo = _user_repo(db_session)
    result = repo.get_by_email("nope@example.com")
    assert result is None

def test_user_repo_duplicate_email_raises_safe_error(db_session):
    repo = _user_repo(db_session)
    _create_user(repo, email="dup@example.com")
    from app.core.exceptions import AppError
    with pytest.raises(AppError) as exc_info:
        _create_user(repo, email="dup@example.com")
    # Safe code, not raw SQL
    assert exc_info.value.code == "INTEGRITY_ERROR"

def test_user_repo_exists(db_session):
    repo = _user_repo(db_session)
    user = _create_user(repo, email="exists@example.com")
    assert repo.exists(user.id) is True
    assert repo.exists(999999) is False

def test_user_repo_list(db_session):
    repo = _user_repo(db_session)
    _create_user(repo, email="list1@example.com")
    _create_user(repo, email="list2@example.com")
    results = repo.list(limit=10)
    assert len(results) >= 2

def test_user_repo_list_bounded(db_session):
    """Pagination hard cap: limit cannot exceed 200."""
    repo = _user_repo(db_session)
    results = repo.list(limit=1000)  # should be capped at 200
    assert len(results) <= 200

def test_user_repo_delete(db_session):
    repo = _user_repo(db_session)
    user = _create_user(repo, email="del@example.com")
    uid = user.id
    repo.delete(uid)
    assert repo.get_or_none(uid) is None


# ── ScanRepository ─────────────────────────────────────────────────────────────

def test_scan_repo_create(db_session):
    repo = _scan_repo(db_session)
    scan = _create_scan(repo)
    assert scan.id is not None
    assert scan.scan_uuid is not None

def test_scan_repo_get_by_uuid(db_session):
    repo = _scan_repo(db_session)
    scan = _create_scan(repo)
    found = repo.get_by_uuid(scan.scan_uuid)
    assert found is not None
    assert found.id == scan.id

def test_scan_repo_get_by_uuid_missing(db_session):
    repo = _scan_repo(db_session)
    assert repo.get_by_uuid("non-existent-uuid") is None

def test_scan_repo_list_by_user(db_session):
    user_repo = _user_repo(db_session)
    user = _create_user(user_repo, email="scanuser@example.com")
    scan_repo = _scan_repo(db_session)
    scan_repo.create(
        target_url="https://a.com", target_hostname="a.com",
        status=SCAN_STATUS_CREATED, user_id=user.id,
    )
    scan_repo.create(
        target_url="https://b.com", target_hostname="b.com",
        status=SCAN_STATUS_CREATED, user_id=user.id,
    )
    scans = scan_repo.list_by_user(user.id)
    assert len(scans) == 2

def test_scan_repo_update_status(db_session):
    repo = _scan_repo(db_session)
    scan = _create_scan(repo)
    repo.update_status(scan, SCAN_STATUS_COMPLETED)
    assert scan.status == SCAN_STATUS_COMPLETED

def test_scan_repo_invalid_status_raises(db_session):
    repo = _scan_repo(db_session)
    scan = _create_scan(repo)
    with pytest.raises(ValueError):
        repo.update_status(scan, "INVALID_STATUS")

def test_scan_repo_list_by_status(db_session):
    repo = _scan_repo(db_session)
    repo.create(
        target_url="https://c.com", target_hostname="c.com",
        status=SCAN_STATUS_FAILED, user_id=None,
    )
    results = repo.list_by_status(SCAN_STATUS_FAILED)
    assert len(results) >= 1
    assert all(s.status == SCAN_STATUS_FAILED for s in results)


# ── FindingRepository ──────────────────────────────────────────────────────────

def _add_finding(db, scan_id, severity="HIGH", code=None):
    from app.models.finding import Finding
    import uuid
    f = Finding(
        scan_id=scan_id,
        finding_code=code or str(uuid.uuid4())[:20],
        category="security_headers",
        title="Test Finding",
        description="desc",
        severity=severity,
        status=FINDING_STATUS_OPEN,
    )
    db.add(f)
    db.flush()
    return f


def test_finding_repo_create(db_session):
    scan = _create_scan(_scan_repo(db_session))
    repo = _finding_repo(db_session)
    f = repo.create(
        scan_id=scan.id,
        finding_code="HSTS_001",
        category="security_headers",
        title="HSTS Missing",
        description="No HSTS",
        severity=SEVERITY_HIGH,
        status=FINDING_STATUS_OPEN,
    )
    assert f.id is not None

def test_finding_repo_list_by_scan(db_session):
    scan = _create_scan(_scan_repo(db_session))
    for _ in range(3):
        _add_finding(db_session, scan.id)
    results = _finding_repo(db_session).list_by_scan(scan.id)
    assert len(results) == 3

def test_finding_repo_list_by_severity(db_session):
    scan = _create_scan(_scan_repo(db_session))
    _add_finding(db_session, scan.id, severity="CRITICAL")
    _add_finding(db_session, scan.id, severity="HIGH")
    _add_finding(db_session, scan.id, severity="LOW")

    critical = _finding_repo(db_session).list_by_severity(scan.id, "CRITICAL")
    assert len(critical) == 1
    assert critical[0].severity == "CRITICAL"

def test_finding_repo_invalid_severity(db_session):
    scan = _create_scan(_scan_repo(db_session))
    with pytest.raises(ValueError):
        _finding_repo(db_session).list_by_severity(scan.id, "ULTRA")

def test_finding_repo_count(db_session):
    scan = _create_scan(_scan_repo(db_session))
    _add_finding(db_session, scan.id)
    _add_finding(db_session, scan.id)
    assert _finding_repo(db_session).count_by_scan(scan.id) == 2


# ── AIReportRepository ─────────────────────────────────────────────────────────

def test_ai_repo_create_and_get(db_session):
    scan = _create_scan(_scan_repo(db_session))
    repo = _ai_repo(db_session)
    report = repo.create(scan_id=scan.id, summary="AI summary", model_name="gpt-4o")
    assert report.id is not None

    fetched = repo.get_by_scan(scan.id)
    assert fetched is not None
    assert fetched.summary == "AI summary"

def test_ai_repo_missing_returns_none(db_session):
    scan = _create_scan(_scan_repo(db_session))
    result = _ai_repo(db_session).get_by_scan(scan.id)
    assert result is None
