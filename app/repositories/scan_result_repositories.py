"""
Certificate, SecurityHeader, Cookie, Redirect, Resource repositories.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.security_header import SecurityHeader
from app.models.cookie import Cookie
from app.models.redirect import Redirect
from app.models.resource import Resource
from app.repositories.base import BaseRepository


class CertificateRepository(BaseRepository[Certificate]):
    def __init__(self, db: Session) -> None:
        super().__init__(Certificate, db)

    def get_by_scan(self, scan_id: int) -> Certificate | None:
        stmt = select(Certificate).where(Certificate.scan_id == scan_id)
        return self.db.execute(stmt).scalar_one_or_none()


class SecurityHeaderRepository(BaseRepository[SecurityHeader]):
    def __init__(self, db: Session) -> None:
        super().__init__(SecurityHeader, db)

    def list_by_scan(self, scan_id: int) -> list[SecurityHeader]:
        stmt = select(SecurityHeader).where(SecurityHeader.scan_id == scan_id)
        return list(self.db.execute(stmt).scalars().all())


class CookieRepository(BaseRepository[Cookie]):
    def __init__(self, db: Session) -> None:
        super().__init__(Cookie, db)

    def list_by_scan(self, scan_id: int) -> list[Cookie]:
        stmt = select(Cookie).where(Cookie.scan_id == scan_id)
        return list(self.db.execute(stmt).scalars().all())


class RedirectRepository(BaseRepository[Redirect]):
    def __init__(self, db: Session) -> None:
        super().__init__(Redirect, db)

    def list_by_scan(self, scan_id: int) -> list[Redirect]:
        stmt = (
            select(Redirect)
            .where(Redirect.scan_id == scan_id)
            .order_by(Redirect.step_number.asc())
        )
        return list(self.db.execute(stmt).scalars().all())


class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, db: Session) -> None:
        super().__init__(Resource, db)

    def list_by_scan(self, scan_id: int) -> list[Resource]:
        stmt = select(Resource).where(Resource.scan_id == scan_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_mixed_content(self, scan_id: int) -> list[Resource]:
        stmt = (
            select(Resource)
            .where(Resource.scan_id == scan_id, Resource.mixed_content.is_(True))
        )
        return list(self.db.execute(stmt).scalars().all())
