"""
Resource model — exactly as defined in Docs/DATABASE.md §16.
Table: resources
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Resource(Base):
    """Externally referenced resource observed during content analysis."""

    __tablename__ = "resources"

    __table_args__ = (
        Index("idx_resources_scan",     "scan_id"),
        Index("idx_resources_hostname", "hostname"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    resource_url:  Mapped[str]       = mapped_column(String(2048), nullable=False)
    resource_type: Mapped[str | None]= mapped_column(String(50),   nullable=True)
    hostname:      Mapped[str | None]= mapped_column(String(255),  nullable=True)
    origin_type:   Mapped[str | None]= mapped_column(String(30),   nullable=True)
    scheme:        Mapped[str | None]= mapped_column(String(10),   nullable=True)
    mixed_content: Mapped[bool]      = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    category:      Mapped[str | None]= mapped_column(String(50),   nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="resources")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Resource id={self.id} scan_id={self.scan_id} "
            f"hostname={self.hostname!r} mixed={self.mixed_content}>"
        )
