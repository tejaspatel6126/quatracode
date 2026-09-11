"""
Base repository with common CRUD helpers.
All repositories inherit from this to avoid code repetition.
"""

import logging
from typing import Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Generic repository providing create / get / list / delete helpers."""

    def __init__(self, model: Type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    # ── Create ────────────────────────────────────────────────────────────────
    def create(self, **kwargs) -> ModelT:
        """
        Create and persist a new instance.
        Wraps IntegrityError to avoid leaking raw SQL to callers.
        """
        instance = self.model(**kwargs)
        try:
            self.db.add(instance)
            self.db.flush()
            return instance
        except IntegrityError as exc:
            self.db.rollback()
            # Log detailed error internally; surface only a safe message
            logger.warning(
                "IntegrityError creating %s: %s",
                self.model.__name__,
                type(exc).__name__,
            )
            raise AppError(
                code="INTEGRITY_ERROR",
                message=f"Could not create {self.model.__name__}: constraint violation.",
                status_code=409,
            ) from exc

    # ── Get by PK ─────────────────────────────────────────────────────────────
    def get(self, record_id: int) -> ModelT:
        """Return the record or raise NotFoundError."""
        instance = self.db.get(self.model, record_id)
        if instance is None:
            raise NotFoundError(f"{self.model.__name__} with id={record_id} not found.")
        return instance

    def get_or_none(self, record_id: int) -> ModelT | None:
        return self.db.get(self.model, record_id)

    # ── List (bounded) ────────────────────────────────────────────────────────
    def list(self, limit: int = 50, offset: int = 0) -> list[ModelT]:
        """Return paginated list ordered by primary key."""
        stmt = (
            select(self.model)
            .order_by(self.model.id)  # type: ignore[attr-defined]
            .limit(min(limit, 200))   # hard cap — never load unbounded sets
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Delete ────────────────────────────────────────────────────────────────
    def delete(self, record_id: int) -> None:
        instance = self.get(record_id)
        try:
            self.db.delete(instance)
            self.db.flush()
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.warning("Error deleting %s id=%s: %s", self.model.__name__, record_id, exc)
            raise

    # ── Exists ────────────────────────────────────────────────────────────────
    def exists(self, record_id: int) -> bool:
        return self.db.get(self.model, record_id) is not None
