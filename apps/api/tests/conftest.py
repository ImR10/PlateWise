"""Shared pytest fixtures for database tests.

Design:

* Tests run against a dedicated ``*_test`` database so they never touch the
  development database. The name is derived from ``TEST_DATABASE_URL`` or, if
  unset, from ``DATABASE_URL`` / application settings with a ``_test`` suffix
  appended to the database name.
* The schema is built by running the *real* Alembic migration to ``head``
  (this doubles as a migration smoke test), so the tests validate exactly what
  production will deploy.
* Each test runs inside a transaction that is rolled back on teardown, giving
  fast, fully-isolated tests. ``join_transaction_mode="create_savepoint"``
  means even code that calls ``session.commit()`` is contained and undone.

Database tests are skipped automatically if PostgreSQL is unreachable, so the
non-database tests (e.g. the health check) still run in constrained
environments.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import settings

API_ROOT = Path(__file__).resolve().parent.parent


def _test_database_url() -> str:
    """Resolve the URL of the dedicated test database."""
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = os.getenv("DATABASE_URL", settings.database_url)
    url = make_url(base)
    db_name = url.database or "platewise"
    if not db_name.endswith("_test"):
        db_name = f"{db_name}_test"
    return url.set(database=db_name).render_as_string(hide_password=False)


def _ensure_database_exists(url_str: str) -> None:
    """Create the target database if it does not already exist."""
    url = make_url(url_str)
    maintenance = url.set(database="postgres")
    engine = create_engine(maintenance, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        engine.dispose()


def _reset_schema(engine: Engine) -> None:
    """Drop and recreate the public schema for a clean slate."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _alembic_config(url_str: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url_str)
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    return _test_database_url()


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    """Session-scoped engine bound to a freshly-migrated test database."""
    try:
        _ensure_database_exists(database_url)
    except OperationalError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"PostgreSQL is not reachable for database tests: {exc}")

    engine = create_engine(database_url, pool_pre_ping=True)
    _reset_schema(engine)
    command.upgrade(_alembic_config(database_url), "head")
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """Function-scoped session wrapped in a transaction that is rolled back."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
