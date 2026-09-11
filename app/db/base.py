"""
SQLAlchemy declarative base.
All ORM models must inherit from Base.
No project-specific models are defined here (Phase 02+).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide declarative base for all SQLAlchemy models."""
    pass
