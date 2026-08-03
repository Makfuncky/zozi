from datetime import datetime
from typing import Optional
import uuid as _uuid

from sqlalchemy import Boolean, DateTime, Integer, Text, func, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import Index


class AuditMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )

    @declared_attr
    def created_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(Integer, nullable=True, index=True)

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(Integer, nullable=True, index=True)

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=1, server_default="1")


class SoftDeleteMixin:
    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(
            Boolean,
            default=False,
            server_default="false",
            nullable=False,
            index=True,
        )

    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def deleted_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(Integer, nullable=True)

    @declared_attr
    def delete_reason(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True)

    def soft_delete(self, deleted_by: Optional[int] = None, reason: Optional[str] = None):
        self.is_deleted = True
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
        self.delete_reason = reason

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.delete_reason = None


class TenantMixin:
    """Country-isolation + public-ref columns (Constitution §2.9).

    Every country-scoped table inherits this mixin so that:
    - ``country_code`` VARCHAR(3) is present for PostgreSQL Row-Level Security.
    - ``uuid`` provides a stable public identifier (never expose the integer PK).
    - ``is_active`` flags disabled rows without soft-deleting.
    - ``version`` supports optimistic locking on concurrent edits.
    """
    __abstract__ = True

    @declared_attr
    def uuid(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(36), nullable=True, unique=True, index=True)

    @declared_attr
    def country_code(cls) -> Mapped[str]:
        return mapped_column(String(3), nullable=False, index=True, default="OMR")

    @declared_attr
    def is_active(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=True, nullable=False, server_default="true", index=True)

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=1, server_default="1")


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
