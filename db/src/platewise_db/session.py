import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg://platewise:platewise_dev_password@db:5432/platewise"


def get_database_url() -> str:
    """Return the configured persistence URL without depending on the API package."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
