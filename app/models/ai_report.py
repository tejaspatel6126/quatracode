"""
AIReport model — exactly as defined in Docs/DATABASE.md §17.
Table: ai_reports  (1:1 with scans — unique constraint on scan_id)

Security requirements:
  - AI output must never overwrite authoritative findings.
  - AI-generated text is clearly separated from scanner evidence.
  - No AI provider secrets are stored here.
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIReport(Base):
    """
    AI-generated explanations for a scan.
    Always derived from structured scanner evidence — never authoritative on its own.
    """

    __tablename__ = "ai_reports"

    __table_args__ = (
        UniqueConstraint("scan_id", name="uq_ai_report_scan"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    summary:         Mapped[str | None]  = mapped_column(Text,         nullable=True)
    explanation:     Mapped[str | None]  = mapped_column(Text,         nullable=True)  # LONGTEXT
    recommendations: Mapped[dict | None] = mapped_column(JSON,         nullable=True)
    model_name:      Mapped[str | None]  = mapped_column(String(100),  nullable=True)
    prompt_version:  Mapped[str | None]  = mapped_column(String(30),   nullable=True)
    generated_at:    Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="ai_report")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<AIReport id={self.id} scan_id={self.scan_id} "
            f"model={self.model_name!r}>"
        )
