"""
SecurityHeader model — exactly as defined in Docs/DATABASE.md §12.
Table: security_headers
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SecurityHeader(Base):
    """Observed HTTP security header for a scan."""

    __tablename__ = "security_headers"

    __table_args__ = (
        Index("idx_headers_scan", "scan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    header_name:  Mapped[str]       = mapped_column(String(255), nullable=False)
    header_value: Mapped[str | None]= mapped_column(Text,        nullable=True)
    present:      Mapped[bool]      = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    evaluation:   Mapped[str | None]= mapped_column(String(30),  nullable=True)
    notes:        Mapped[str | None]= mapped_column(Text,        nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="security_headers")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<SecurityHeader id={self.id} scan_id={self.scan_id} "
            f"name={self.header_name!r} present={self.present}>"
        )
