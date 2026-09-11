"""
Shared pytest fixtures and configuration.
Tests must never require live database credentials or AI keys.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a FastAPI test client for the full application."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
