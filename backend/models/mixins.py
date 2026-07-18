from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean
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

    deleted_by = relationship("User", foreign_keys=[deleted_by_id])

    def soft_delete(self, deleted_by: Optional[int] = None):
        self.is_deleted = True
        self.deleted_at = _utcnow()
        self.deleted_by_id = deleted_by

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by_id = None

