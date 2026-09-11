"""
Alembic migration environment.
Configured to use:
  - DATABASE_URL from application settings (env var / .env file)
  - app.db.base.Base as the target metadata for autogenerate

Fix note:
  Alembic uses Python's ConfigParser which treats '%' as interpolation syntax.
  URL-encoded passwords (e.g. R%40j%40t2004) would raise:
      ValueError: invalid interpolation syntax in '...%40...'
  Resolution: the engine is created directly from settings.DATABASE_URL using
  SQLAlchemy's create_engine(), bypassing ConfigParser entirely.
  config.set_main_option() is NEVER called with the live database URL.
"""

from logging.config import fileConfig

import sqlalchemy
from sqlalchemy import pool

from alembic import context

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# ── Python logging via alembic.ini ────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Application settings ──────────────────────────────────────────────────────
# Load settings here so DATABASE_URL is available without going through
# ConfigParser (which would corrupt URL-encoded characters such as %40).
from app.core.config import get_settings as _get_settings  # noqa: E402

_settings = _get_settings()

# ── Target metadata for autogenerate ─────────────────────────────────────────
# Import Base and then all model modules so every table is registered.
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402, F401

target_metadata = Base.metadata


# ── Migration runners ─────────────────────────────────────────────────────────

def _get_url() -> str:
    """
    Return the database URL to use for migrations.

    Priority:
      1. If test code has injected a real (non-placeholder) URL via
         alembic_cfg.set_main_option("sqlalchemy.url", ...) before calling
         alembic.command.upgrade(), use that value directly.
      2. Otherwise use settings.DATABASE_URL loaded from .env.

    The URL is NEVER written back into ConfigParser to avoid the
    '%'-interpolation bug.
    """
    ini_url = config.get_main_option("sqlalchemy.url") or ""
    placeholder = "driver://user:pass@localhost/dbname"
    if ini_url and ini_url != placeholder:
        # Caller (e.g. test) has provided a real URL — respect it.
        return ini_url
    return _settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL emitted without a live connection)."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (requires a live DB connection).

    The engine is created directly from the URL string — NOT via
    engine_from_config() — so that ConfigParser interpolation is never
    triggered on URL-encoded characters in the password.
    """
    url = _get_url()
    connectable = sqlalchemy.create_engine(
        url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
