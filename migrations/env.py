"""
Alembic migration environment.
Configured to use:
  - DATABASE_URL from application settings (env var)
  - app.db.base.Base as the target metadata for autogenerate
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# ── Python logging via alembic.ini ────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Inject DATABASE_URL from application settings ─────────────────────────────
# Only override if the caller hasn't already set a real URL.
# This allows test code to inject a SQLite URL via alembic_cfg.set_main_option()
# before invoking alembic.command.upgrade/downgrade.
_current_url = config.get_main_option("sqlalchemy.url") or ""
_is_placeholder = _current_url in ("", "driver://user:pass@localhost/dbname")

if _is_placeholder:
    from app.core.config import get_settings as _get_settings  # noqa: E402
    config.set_main_option("sqlalchemy.url", _get_settings().DATABASE_URL)

# ── Target metadata for autogenerate ─────────────────────────────────────────
# Import Base so that all models registered under it are visible to Alembic.
# Phase 02+ models will be imported in app/db/base.py — add imports there.
from app.db.base import Base  # noqa: E402

# Import all model modules so their tables are registered with Base.metadata
import app.models  # noqa: E402, F401

target_metadata = Base.metadata


# ── Migration runners ─────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations in offline mode (no live DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
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
    """Run migrations in online mode (requires a live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
