"""
User model — exactly as defined in Docs/DATABASE.md §5.
Table: users
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    """
    Application user.

    Security requirements (DATABASE.md §5.2):
      - Passwords are NEVER stored in plaintext.
      - Only password_hash is stored.
      - password_hash must never be returned in API responses.
    """

    __tablename__ = "users"

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        "id",
        # BIGINT UNSIGNED AUTO_INCREMENT
        primary_key=True,
        autoincrement=True,
    )

    # ── Columns ────────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,           # enforced at DB level
        index=True,            # users.email index (DATABASE.md §20)
    )

    # nullable=True allows OAuth-style accounts without a local password
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    scans: Mapped[list["Scan"]] = relationship(  # noqa: F821
        "Scan",
        back_populates="user",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} active={self.is_active}>"
