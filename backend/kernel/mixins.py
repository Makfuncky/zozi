"""Kernel-level mixins — pure business primitives with no external dependencies."""

from sqlalchemy import Column, DateTime, func


class TimestampMixin:
    """Standard timestamp columns (created_at, updated_at) with DB-side defaults.

    Law 229: All business tables MUST have created_at/updated_at via TimestampMixin.
    """

    __abstract__ = True

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)