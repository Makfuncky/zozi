from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class VersionMixin:
    """Optimistic-lock revision counter (Constitution §2.9).

    Extracted so AuditMixin and TenantMixin no longer define a duplicate
    ``version`` column (which collided when both were composed on one model).
    """

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(
            Integer, nullable=False, default=1, server_default="1"
        )


class TenantMixin:
    @declared_attr
    def country_code(cls) -> Mapped[str]:
        return mapped_column(String(10), nullable=False, index=True)


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
