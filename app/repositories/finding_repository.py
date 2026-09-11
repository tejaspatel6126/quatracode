"""
Finding repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import Finding, SEVERITIES
from app.repositories.base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    def __init__(self, db: Session) -> None:
        super().__init__(Finding, db)

    def list_by_scan(
        self, scan_id: int, limit: int = 200, offset: int = 0
    ) -> list[Finding]:
        stmt = (
            select(Finding)
            .where(Finding.scan_id == scan_id)
            .order_by(Finding.created_at.asc())
            .limit(min(limit, 500))
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_severity(
        self, scan_id: int, severity: str
    ) -> list[Finding]:
        if severity not in SEVERITIES:
            raise ValueError(f"Invalid severity: {severity!r}")
        stmt = (
            select(Finding)
            .where(Finding.scan_id == scan_id, Finding.severity == severity)
            .order_by(Finding.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def count_by_scan(self, scan_id: int) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Finding).where(Finding.scan_id == scan_id)
        return self.db.execute(stmt).scalar_one()
