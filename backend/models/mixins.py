from datetime import datetime
from typing import Optional
import uuid as _uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, String, Text
from sqlalchemy.orm import relationship

from . import Base
from utils.datetime_utils import utcnow as _utcnow


class AuditMixin:
    """Standard audit columns for all models that require tracking."""
    __abstract__ = True

    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class SoftDeleteMixin:
    """Standard soft-delete columns for models that support archival."""
    __abstract__ = True

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    delete_reason = Column(Text, nullable=True)

    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    def soft_delete(self, deleted_by: Optional[int] = None, reason: Optional[str] = None):
        self.is_deleted = True
        self.deleted_at = _utcnow()
        self.deleted_by_id = deleted_by
        self.delete_reason = reason

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by_id = None
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

    uuid = Column(String(36), nullable=False, unique=False, index=True,
                  default=lambda: str(_uuid.uuid4()))
    country_code = Column(String(3), nullable=False, index=True, default="OMR")
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)

