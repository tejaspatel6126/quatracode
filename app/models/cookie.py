"""
Cookie model — exactly as defined in Docs/DATABASE.md §14.
Table: cookies

Note: Cookie VALUES are NOT stored (sensitive). Only security attributes.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cookie(Base):
    """Publicly observable cookie security configuration observed during a scan."""

    __tablename__ = "cookies"

    __table_args__ = (
        Index("idx_cookies_scan", "scan_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    scan_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(BigInteger, "mysql"),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )

    cookie_name: Mapped[str]       = mapped_column(String(255), nullable=False)
    secure:      Mapped[bool | None] = mapped_column(Boolean,  nullable=True)
    http_only:   Mapped[bool | None] = mapped_column(Boolean,  nullable=True)
    same_site:   Mapped[str | None]  = mapped_column(String(20), nullable=True)
    domain:      Mapped[str | None]  = mapped_column(String(255), nullable=True)
    path:        Mapped[str | None]  = mapped_column(String(255), nullable=True)
    expires_at:  Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_age:     Mapped[int | None]  = mapped_column(BigInteger, nullable=True)
    evaluation:  Mapped[str | None]  = mapped_column(String(30), nullable=True)
    notes:       Mapped[str | None]  = mapped_column(Text,       nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="cookies")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Cookie id={self.id} scan_id={self.scan_id} "
            f"name={self.cookie_name!r} secure={self.secure}>"
        )
