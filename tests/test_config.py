"""
Tests for application configuration loading.
Must never require production credentials.
"""

from app.core.config import Settings, get_settings


def test_settings_load_defaults():
    """Settings must initialise with safe defaults."""
    s = Settings()
    assert s.APP_NAME
    assert s.APP_ENV in ("development", "production", "test")
    assert s.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def test_settings_cors_list():
    """CORS origins must be returned as a list."""
    s = Settings(CORS_ORIGINS="http://localhost:8000,http://127.0.0.1:8000")
    origins = s.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) == 2
    assert "http://localhost:8000" in origins


def test_settings_singleton():
    """get_settings() must always return the same instance."""
    a = get_settings()
    b = get_settings()
    assert a is b


def test_settings_no_wildcard_cors_by_default():
    """Wildcard CORS must not appear in default configuration."""
    s = Settings()
    assert "*" not in s.CORS_ORIGINS


def test_settings_ai_disabled_by_default():
    """AI must be disabled in Phase 01."""
    s = Settings()
    assert s.AI_ENABLED is False


def test_settings_debug_false_by_default():
    """Debug mode must default to False."""
    s = Settings()
    assert s.DEBUG is False
