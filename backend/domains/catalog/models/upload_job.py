"""Upload job model.

Tracks bulk/async file uploads (CSV imports, media bulk upload, etc.).
Country-scoped via ``country_code`` and carries the platform audit +
soft-delete contract (uuid, version, is_deleted, created_by, updated_by) used
across the ORM models.
"""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UUID,
)
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["UploadJob"]

class UploadJob(Base):
    __tablename__ = "upload_jobs"

    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, default=False, server_default="false", nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(1024), nullable=True)
    content_type = Column(String(128), nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    error_log = Column(Text, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_upload_jobs_country_created", "country_code", "created_at"),
        {"schema": "catalog"},
    )
