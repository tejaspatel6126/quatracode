"""
Scan model — exactly as defined in Docs/DATABASE.md §6.
Table: scans

Status values (DATABASE.md §6.2):
  created | validating | queued | scanning | analyzing | scoring | ai_processing | completed | failed
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    DECIMAL,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

# ── Allowed scan status values (DATABASE.md §6.2) ─────────────────────────────
SCAN_STATUS_CREATED       = "created"
SCAN_STATUS_VALIDATING    = "validating"
SCAN_STATUS_QUEUED        = "queued"
SCAN_STATUS_SCANNING      = "scanning"
SCAN_STATUS_ANALYZING     = "analyzing"
SCAN_STATUS_SCORING       = "scoring"
SCAN_STATUS_AI_PROCESSING = "ai_processing"
SCAN_STATUS_COMPLETED     = "completed"
SCAN_STATUS_FAILED        = "failed"

SCAN_STATUSES = {
    SCAN_STATUS_CREATED,
    SCAN_STATUS_VALIDATING,
    SCAN_STATUS_QUEUED,
    SCAN_STATUS_SCANNING,
    SCAN_STATUS_ANALYZING,
    SCAN_STATUS_SCORING,
    SCAN_STATUS_AI_PROCESSING,
    SCAN_STATUS_COMPLETED,
    SCAN_STATUS_FAILED,
}


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Scan(TimestampMixin, Base):
    """
    Central scan record.
    Every security assessment creates exactly one Scan.
    Database storage does NOT constitute SSRF authorization (DATABASE.md §11 note).
    """

    __tablename__ = "scans"

    __table_args__ = (
        Index("idx_scans_hostname", "target_hostname"),
        Index("idx_scans_status", "status"),
        Index("idx_scans_user", "user_id"),
        Index("idx_scans_created", "created_at"),
        Index("idx_scans_uuid", "scan_uuid"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Public identifier ──────────────────────────────────────────────────────
    scan_uuid: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
        unique=True,
        default=_new_uuid,
    )

    # ── Ownership (nullable → anonymous scanning allowed) ──────────────────────
    user_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Target ────────────────────────────────────────────────────────────────
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_hostname: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=SCAN_STATUS_CREATED,
        server_default=SCAN_STATUS_CREATED,
    )

    # ── Scoring summary ───────────────────────────────────────────────────────
    security_score: Mapped[float | None] = mapped_column(
        DECIMAL(5, 2), nullable=True
    )
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Finding counters ──────────────────────────────────────────────────────
    total_findings: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    critical_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    high_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    medium_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    low_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    info_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    passed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # ── Lifecycle timestamps ──────────────────────────────────────────────────
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="scans")  # noqa: F821

    findings: Mapped[list["Finding"]] = relationship(  # noqa: F821
        "Finding", back_populates="scan", cascade="all, delete-orphan", lazy="select"
    )
    certificate: Mapped["Certificate | None"] = relationship(  # noqa: F821
        "Certificate", back_populates="scan", uselist=False,
        cascade="all, delete-orphan", lazy="select"
    )
    security_headers: Mapped[list["SecurityHeader"]] = relationship(  # noqa: F821
        "SecurityHeader", back_populates="scan",
        cascade="all, delete-orphan", lazy="select"
    )
    cookies: Mapped[list["Cookie"]] = relationship(  # noqa: F821
        "Cookie", back_populates="scan", cascade="all, delete-orphan", lazy="select"
    )
    redirects: Mapped[list["Redirect"]] = relationship(  # noqa: F821
        "Redirect", back_populates="scan", cascade="all, delete-orphan", lazy="select"
    )
    resources: Mapped[list["Resource"]] = relationship(  # noqa: F821
        "Resource", back_populates="scan", cascade="all, delete-orphan", lazy="select"
    )
    ai_report: Mapped["AIReport | None"] = relationship(  # noqa: F821
        "AIReport", back_populates="scan", uselist=False,
        cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Scan id={self.id} uuid={self.scan_uuid!r} "
            f"status={self.status!r} target={self.target_hostname!r}>"
        )
