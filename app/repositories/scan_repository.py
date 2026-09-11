"""
Scan repository.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan import Scan, SCAN_STATUSES
from app.repositories.base import BaseRepository


class ScanRepository(BaseRepository[Scan]):
    def __init__(self, db: Session) -> None:
        super().__init__(Scan, db)

    # ── Ownership ─────────────────────────────────────────────────────────────
    def get_by_uuid(self, scan_uuid: str) -> Scan | None:
        stmt = select(Scan).where(Scan.scan_uuid == scan_uuid)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Scan]:
        stmt = (
            select(Scan)
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(min(limit, 200))
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Status ────────────────────────────────────────────────────────────────
    def list_by_status(
        self, status: str, limit: int = 50, offset: int = 0
    ) -> list[Scan]:
        stmt = (
            select(Scan)
            .where(Scan.status == status)
            .order_by(Scan.created_at.desc())
            .limit(min(limit, 200))
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_status(self, scan: Scan, status: str) -> Scan:
        if status not in SCAN_STATUSES:
            raise ValueError(f"Invalid scan status: {status!r}")
        scan.status = status
        self.db.flush()
        return scan

    def mark_started(self, scan: Scan) -> Scan:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        scan.started_at = now
        self.db.flush()
        return scan

    def mark_completed(self, scan: Scan) -> Scan:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        scan.completed_at = now
        self.db.flush()
        return scan
