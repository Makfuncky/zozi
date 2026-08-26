from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class AuditMixin:
    """Standard audit columns for all models that require tracking."""
    __abstract__ = True

    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("core.users.id"), nullable=True, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("core.users.id"), nullable=True, index=True)

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class SoftDeleteMixin:
    """Standard soft-delete columns for models that support archival."""
    __abstract__ = True

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)

    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    def soft_delete(self, deleted_by: Optional[int] = None):
        self.is_deleted = True
        self.deleted_at = _utcnow()
        self.deleted_by_id = deleted_by

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by_id = None


class TenantMixin:
    """Per-tenant (country-scoped) column contract.

    Provides ``country_code`` so country-scoped models do not each redeclare it.
    Restored after the db/mixins.py -> models/mixins.py split dropped it.
    """

    __abstract__ = True
    country_code = Column(String(2), nullable=False, index=True)


class VersionMixin:
    """Optimistic-lock revision counter (Constitution §2.9).

    Relocated from ``db/mixins.py`` so that ``models.mixins`` is the single
    canonical mixins location. Uses the modern ``Mapped``/``declared_attr``
    idiom so it composes with other mixins on the same model class.
    """

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(
            Integer, nullable=False, default=1, server_default="1"
        )


