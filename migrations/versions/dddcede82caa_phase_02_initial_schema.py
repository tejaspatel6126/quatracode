"""phase_02_initial_schema

Creates all 9 tables defined in Docs/DATABASE.md §34 (MVP database):
  users, scans, findings, certificates, security_headers,
  cookies, redirects, resources, ai_reports

Revision ID: dddcede82caa
Revises:
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "dddcede82caa"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # ── scans ──────────────────────────────────────────────────────────────────
    op.create_table(
        "scans",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_uuid", sa.CHAR(36), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("target_hostname", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), server_default="created", nullable=False),
        sa.Column("security_score", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("total_findings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("critical_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("high_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("medium_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("info_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("passed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                name="fk_scans_user", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_scans"),
        sa.UniqueConstraint("scan_uuid", name="uq_scans_uuid"),
    )
    op.create_index("idx_scans_hostname", "scans", ["target_hostname"])
    op.create_index("idx_scans_status",   "scans", ["status"])
    op.create_index("idx_scans_user",     "scans", ["user_id"])
    op.create_index("idx_scans_created",  "scans", ["created_at"])
    op.create_index("idx_scans_uuid",     "scans", ["scan_uuid"], unique=True)

    # ── findings ───────────────────────────────────────────────────────────────
    op.create_table(
        "findings",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("finding_code", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("confidence", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("impact", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_findings_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_findings"),
    )
    op.create_index("idx_findings_scan",     "findings", ["scan_id"])
    op.create_index("idx_findings_category", "findings", ["category"])
    op.create_index("idx_findings_severity", "findings", ["severity"])
    op.create_index("idx_findings_code",     "findings", ["finding_code"])

    # ── certificates ──────────────────────────────────────────────────────────
    op.create_table(
        "certificates",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("not_before", sa.DateTime(), nullable=True),
        sa.Column("not_after", sa.DateTime(), nullable=True),
        sa.Column("hostname_match", sa.Boolean(), nullable=True),
        sa.Column("self_signed", sa.Boolean(), nullable=True),
        sa.Column("san_entries", sa.JSON(), nullable=True),
        sa.Column("chain_valid", sa.Boolean(), nullable=True),
        sa.Column("protocol_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_certificates_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_certificates"),
        sa.UniqueConstraint("scan_id", name="uq_certificate_scan"),
    )

    # ── security_headers ──────────────────────────────────────────────────────
    op.create_table(
        "security_headers",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("header_name", sa.String(255), nullable=False),
        sa.Column("header_value", sa.Text(), nullable=True),
        sa.Column("present", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("evaluation", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_headers_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_security_headers"),
    )
    op.create_index("idx_headers_scan", "security_headers", ["scan_id"])

    # ── cookies ───────────────────────────────────────────────────────────────
    op.create_table(
        "cookies",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("cookie_name", sa.String(255), nullable=False),
        sa.Column("secure", sa.Boolean(), nullable=True),
        sa.Column("http_only", sa.Boolean(), nullable=True),
        sa.Column("same_site", sa.String(20), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("path", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_age", sa.BigInteger(), nullable=True),
        sa.Column("evaluation", sa.String(30), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_cookies_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_cookies"),
    )
    op.create_index("idx_cookies_scan", "cookies", ["scan_id"])

    # ── redirects ─────────────────────────────────────────────────────────────
    op.create_table(
        "redirects",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("step_number", sa.BigInteger(), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.SmallInteger(), nullable=False),
        sa.Column("location_url", sa.String(2048), nullable=True),
        sa.Column("destination_scheme", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_redirects_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_redirects"),
    )
    op.create_index("idx_redirects_scan", "redirects", ["scan_id"])

    # ── resources ─────────────────────────────────────────────────────────────
    op.create_table(
        "resources",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("resource_url", sa.String(2048), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("origin_type", sa.String(30), nullable=True),
        sa.Column("scheme", sa.String(10), nullable=True),
        sa.Column("mixed_content", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_resources_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_resources"),
    )
    op.create_index("idx_resources_scan",     "resources", ["scan_id"])
    op.create_index("idx_resources_hostname", "resources", ["hostname"])

    # ── ai_reports ────────────────────────────────────────────────────────────
    op.create_table(
        "ai_reports",
        sa.Column("id", sa.BigInteger().with_variant(sa.BigInteger, "mysql"),
                  autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.BigInteger(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(30), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"],
                                name="fk_ai_reports_scan", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_reports"),
        sa.UniqueConstraint("scan_id", name="uq_ai_report_scan"),
    )
    op.create_index("idx_ai_reports_scan", "ai_reports", ["scan_id"])


def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("ai_reports")
    op.drop_table("resources")
    op.drop_table("redirects")
    op.drop_table("cookies")
    op.drop_table("security_headers")
    op.drop_table("certificates")
    op.drop_table("findings")
    op.drop_table("scans")
    op.drop_table("users")
