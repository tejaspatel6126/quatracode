"""
Shared mixin for timestamp columns.
All major models include created_at / updated_at stored as UTC DATETIME.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # store as naive UTC


class TimestampMixin:
    """Adds created_at and updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
