"""
Finding model — exactly as defined in Docs/DATABASE.md §7.
Table: findings

Severity values (DATABASE.md §9): CRITICAL | HIGH | MEDIUM | LOW | INFO | PASS
Finding categories (DATABASE.md §8):
  transport_security | security_headers | cookies | redirects |
  content_security | third_party_resources | other
"""

from sqlalchemy import JSON, DECIMAL, BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

# ── Severity constants (DATABASE.md §9) ───────────────────────────────────────
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH     = "HIGH"
SEVERITY_MEDIUM   = "MEDIUM"
SEVERITY_LOW      = "LOW"
SEVERITY_INFO     = "INFO"
SEVERITY_PASS     = "PASS"

SEVERITIES = {
    SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM,
    SEVERITY_LOW, SEVERITY_INFO, SEVERITY_PASS,
}

# ── Category constants (DATABASE.md §8) ───────────────────────────────────────
CATEGORY_TRANSPORT_SECURITY  = "transport_security"
CATEGORY_SECURITY_HEADERS    = "security_headers"
CATEGORY_COOKIES             = "cookies"
CATEGORY_REDIRECTS           = "redirects"
CATEGORY_CONTENT_SECURITY    = "content_security"
CATEGORY_THIRD_PARTY         = "third_party_resources"
CATEGORY_OTHER               = "other"

# Finding status values
FINDING_STATUS_OPEN     = "open"
FINDING_STATUS_ACCEPTED = "accepted"
FINDING_STATUS_RESOLVED = "resolved"


class Finding(TimestampMixin, Base):
    """
    Security finding produced by a scanner.
    AI must NOT overwrite severity, evidence, or finding_code.
    """

    __tablename__ = "findings"

    __table_args__ = (
        Index("idx_findings_scan",     "scan_id"),
        Index("idx_findings_category", "category"),
        Index("idx_findings_severity", "severity"),
        Index("idx_findings_code",     "finding_code"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Foreign key ────────────────────────────────────────────────────────────
    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Columns (DATABASE.md §7.1) ────────────────────────────────────────────
    finding_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category:     Mapped[str] = mapped_column(String(50),  nullable=False)
    title:        Mapped[str] = mapped_column(String(255), nullable=False)
    description:  Mapped[str] = mapped_column(Text,        nullable=False)
    evidence:     Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity:     Mapped[str] = mapped_column(String(20),  nullable=False)
    confidence:   Mapped[float | None] = mapped_column(DECIMAL(5, 4), nullable=True)
    impact:       Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False,
        default=FINDING_STATUS_OPEN, server_default=FINDING_STATUS_OPEN,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Finding id={self.id} code={self.finding_code!r} "
            f"severity={self.severity!r} scan_id={self.scan_id}>"
        )
