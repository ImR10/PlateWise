"""Declarative base and shared metadata for all PlateWise ORM models.

A single :class:`Base` is shared across every model module so that
``Base.metadata`` describes the whole schema. A deterministic naming
convention is attached to the metadata so that constraints and indexes
receive stable, predictable names in both the ORM and Alembic migrations.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Deterministic naming convention keeps constraint/index names stable and
# human-readable, which makes Alembic autogeneration and manual migrations
# reproducible instead of relying on database-generated identifiers.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models in the PlateWise database."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
