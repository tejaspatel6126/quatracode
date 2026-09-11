"""
AI report repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_report import AIReport
from app.repositories.base import BaseRepository


class AIReportRepository(BaseRepository[AIReport]):
    def __init__(self, db: Session) -> None:
        super().__init__(AIReport, db)

    def get_by_scan(self, scan_id: int) -> AIReport | None:
        stmt = select(AIReport).where(AIReport.scan_id == scan_id)
        return self.db.execute(stmt).scalar_one_or_none()
