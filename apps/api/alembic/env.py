import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db import models  # noqa: F401  (registers all models on Base.metadata)
from app.db.base import Base

config = context.config

# URL resolution order:
#   1. A URL already set on the Alembic config (e.g. injected by the test
#      harness to target a dedicated ``*_test`` database).
#   2. The DATABASE_URL environment variable.
#   3. Application settings.
# The alembic.ini placeholder ("driver://...") is treated as "unset".
_configured_url = config.get_main_option("sqlalchemy.url")
if not _configured_url or _configured_url.startswith("driver://"):
    _configured_url = os.getenv("DATABASE_URL", settings.database_url)
    config.set_main_option("sqlalchemy.url", _configured_url)

if config.config_file_name is not None:
    # Migration setup may run in-process (notably in the integration-test
    # harness); preserve application loggers so importer observability is not
    # silently disabled after Alembic configures its own logger.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
