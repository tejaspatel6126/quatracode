"""
Model registry.
Import every model here so SQLAlchemy's Base.metadata knows about all tables.
Alembic's env.py imports Base, which imports this module automatically via db/base_all.py.
"""

from app.models.ai_report import AIReport
from app.models.certificate import Certificate
from app.models.cookie import Cookie
from app.models.finding import Finding
from app.models.mixins import TimestampMixin
from app.models.redirect import Redirect
from app.models.resource import Resource
from app.models.scan import Scan
from app.models.security_header import SecurityHeader
from app.models.user import User

__all__ = [
    "User",
    "Scan",
    "Finding",
    "Certificate",
    "SecurityHeader",
    "Cookie",
    "Redirect",
    "Resource",
    "AIReport",
    "TimestampMixin",
]
