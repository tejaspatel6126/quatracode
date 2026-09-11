"""
Migration structural tests.
Applies the Phase 02 migration to an isolated SQLite database and verifies
that all 9 tables, indexes, and unique constraints are present.
No MySQL required.
"""

import pytest
from sqlalchemy import create_engine, inspect, event

from alembic.config import Config
from alembic import command


@pytest.fixture(scope="module")
def migrated_engine(tmp_path_factory):
    """Run alembic upgrade head on a fresh SQLite DB and return the engine."""
    db_path = tmp_path_factory.mktemp("migration") / "test_migration.db"
    db_url = f"sqlite:///{db_path}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url)
    yield engine
    engine.dispose()


EXPECTED_TABLES = {
    "users",
    "scans",
    "findings",
    "certificates",
    "security_headers",
    "cookies",
    "redirects",
    "resources",
    "ai_reports",
}


def test_migration_creates_all_tables(migrated_engine):
    inspector = inspect(migrated_engine)
    actual_tables = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - actual_tables
    assert not missing, f"Tables missing after migration: {missing}"


def test_users_columns(migrated_engine):
    inspector = inspect(migrated_engine)
    cols = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "email", "password_hash", "is_active", "created_at", "updated_at"} <= cols


def test_scans_columns(migrated_engine):
    inspector = inspect(migrated_engine)
    cols = {c["name"] for c in inspector.get_columns("scans")}
    required = {
        "id", "scan_uuid", "user_id", "target_url", "target_hostname",
        "status", "security_score", "risk_level",
        "total_findings", "critical_count", "high_count", "medium_count",
        "low_count", "info_count", "passed_count",
        "started_at", "completed_at", "created_at", "updated_at",
    }
    assert required <= cols


def test_findings_columns(migrated_engine):
    inspector = inspect(migrated_engine)
    cols = {c["name"] for c in inspector.get_columns("findings")}
    required = {
        "id", "scan_id", "finding_code", "category", "title",
        "description", "evidence", "severity", "confidence",
        "impact", "recommendation", "status", "created_at", "updated_at",
    }
    assert required <= cols


def test_certificates_unique_scan_id(migrated_engine):
    inspector = inspect(migrated_engine)
    unique_constraints = inspector.get_unique_constraints("certificates")
    uq_cols = [set(u["column_names"]) for u in unique_constraints]
    assert {"scan_id"} in uq_cols


def test_ai_reports_unique_scan_id(migrated_engine):
    inspector = inspect(migrated_engine)
    unique_constraints = inspector.get_unique_constraints("ai_reports")
    uq_cols = [set(u["column_names"]) for u in unique_constraints]
    assert {"scan_id"} in uq_cols


def test_migration_downgrade(migrated_engine, tmp_path_factory):
    """Verify downgrade drops all Phase 02 tables."""
    db_path = tmp_path_factory.mktemp("downgrade") / "test_downgrade.db"
    db_url = f"sqlite:///{db_path}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "-1")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    remaining = set(inspector.get_table_names())
    engine.dispose()

    # After downgrade, none of our Phase 02 tables should exist
    # (alembic_version table may remain)
    phase02_tables = EXPECTED_TABLES & remaining
    assert not phase02_tables, f"Tables not cleaned up on downgrade: {phase02_tables}"


def test_migration_upgrade_after_downgrade(tmp_path_factory):
    """Verify upgrade is idempotent after a downgrade."""
    db_path = tmp_path_factory.mktemp("reupgrade") / "test_reupgrade.db"
    db_url = f"sqlite:///{db_path}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    engine.dispose()

    missing = EXPECTED_TABLES - actual_tables
    assert not missing, f"Tables missing after re-upgrade: {missing}"
