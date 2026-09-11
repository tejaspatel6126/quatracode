"""
Certificate model — exactly as defined in Docs/DATABASE.md §11.
Table: certificates  (1:1 with scans — unique constraint on scan_id)
"""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Certificate(Base):
    """
    TLS certificate observations for one scan.
    One scan → at most one certificate record (UNIQUE scan_id).
    Does NOT have updated_at — only created_at (DATABASE.md §11.1).
    """

    __tablename__ = "certificates"

    __table_args__ = (
        UniqueConstraint("scan_id", name="uq_certificate_scan"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Foreign key ────────────────────────────────────────────────────────────
    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Columns (DATABASE.md §11.1) ───────────────────────────────────────────
    subject:          Mapped[str | None]  = mapped_column(Text,         nullable=True)
    issuer:           Mapped[str | None]  = mapped_column(Text,         nullable=True)
    serial_number:    Mapped[str | None]  = mapped_column(String(255),  nullable=True)
    not_before:       Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    not_after:        Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hostname_match:   Mapped[bool | None] = mapped_column(Boolean,      nullable=True)
    self_signed:      Mapped[bool | None] = mapped_column(Boolean,      nullable=True)
    san_entries:      Mapped[dict | None] = mapped_column(JSON,         nullable=True)
    chain_valid:      Mapped[bool | None] = mapped_column(Boolean,      nullable=True)
    protocol_summary: Mapped[dict | None] = mapped_column(JSON,         nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    scan: Mapped["Scan"] = relationship("Scan", back_populates="certificate")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Certificate id={self.id} scan_id={self.scan_id} sn={self.serial_number!r}>"
