"""
Redirect model — exactly as defined in Docs/DATABASE.md §15.
Table: redirects
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Redirect(Base):
    """One step in the HTTP redirect chain observed during a scan."""

    __tablename__ = "redirects"

    __table_args__ = (
        Index("idx_redirects_scan", "scan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_number:        Mapped[int]       = mapped_column(BigInteger, nullable=False)
    source_url:         Mapped[str]       = mapped_column(String(2048), nullable=False)
    status_code:        Mapped[int]       = mapped_column(SmallInteger, nullable=False)
    location_url:       Mapped[str | None]= mapped_column(String(2048), nullable=True)
    destination_scheme: Mapped[str | None]= mapped_column(String(10),   nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="redirects")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Redirect id={self.id} scan_id={self.scan_id} "
            f"step={self.step_number} status={self.status_code}>"
        )
