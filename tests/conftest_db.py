"""
Shared fixtures for Phase 02 tests.
Uses SQLite in-memory so MySQL is not required in CI/development.
All tests that use 'db_session' run against a real DB engine.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.models  # noqa: F401 — registers all tables with Base.metadata


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped in-memory SQLite engine with all tables created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Enable FK enforcement in SQLite (off by default)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Session:
    """
    Function-scoped transaction that is rolled back after each test.
    This keeps tests isolated without recreating the schema.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
