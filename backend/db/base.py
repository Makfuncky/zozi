"""Declarative base shared by all ORM models.

Defines the canonical ``Base`` (with the production-safe ``_GuardedMetaData``)
so that ``db.base.Base`` and ``models.Base`` are the *same* class with a single
shared ``MetaData``.  ``models`` imports ``Base`` from here (downward edge),
which removes the previous upward ``db -> models`` import cycle.
"""
from __future__ import annotations

import os

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class _GuardedMetaData(MetaData):
    """MetaData that forbids ``create_all`` / ``drop_all`` outside dev/test.

    Implements Constitution §2.7 / ADR-012: ``Base.metadata.create_all()`` is
    for development and test only.  Production schema changes MUST go through
    reviewed Alembic migrations.

    The guard passes through when:
      * ``ALEMBIC_MODE=true`` (sanctioned migration context), **or**
      * the target bind is SQLite (dev / in-memory test), **or**
      * ``APP_ENV`` is not ``production``.

    Every other combination raises ``RuntimeError`` so there is no code path
    that can accidentally ``create_all`` against a PostgreSQL production
    database.
    """

    def _guard(self, operation: str, bind) -> None:
        if os.getenv("ALEMBIC_MODE") == "true":
            return
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            raise RuntimeError(
                f"{operation} is forbidden in production (APP_ENV=production). "
                f"Use a reviewed Alembic migration instead of Base.metadata."
                f"{operation}."
            )
        if bind is not None and bind.dialect.name == "postgresql":
            raise RuntimeError(
                f"{operation} is disabled on PostgreSQL. "
                f"Use a reviewed Alembic migration instead of Base.metadata."
                f"{operation}."
            )

    def create_all(self, *args, **kwargs):
        bind = kwargs.get("bind")
        if bind is None and args:
            bind = args[0]
        self._guard("create_all", bind)
        return super().create_all(*args, **kwargs)

    def drop_all(self, *args, **kwargs):
        bind = kwargs.get("bind")
        if bind is None and args:
            bind = args[0]
        self._guard("drop_all", bind)
        return super().drop_all(*args, **kwargs)


class Base(DeclarativeBase):
    metadata = _GuardedMetaData()


__all__ = ["Base", "_GuardedMetaData"]