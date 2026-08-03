from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin

class MediaAsset(Base, TenantMixin):
    """Tracks all uploaded media assets with 3-tier path structure."""
    __tablename__ = "media_assets"
    __table_args__ = (
        Index("ix_media_assets_entity", "entity_type", "entity_id"),
        Index("ix_media_assets_variant", "entity_id", "variant"), {"schema": "media"})

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True, index=True)

    entity_type = Column(String(20), nullable=False)  # product | supplier | user | article
    entity_id = Column(Integer, nullable=True, index=True)

    variant = Column(String(20), nullable=False)  # original | main | gallery | thumbnail | small
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    is_primary = Column(Boolean, default=False)
    alt_text = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)

    uploaded_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    supplier = relationship("User", foreign_keys="MediaAsset.supplier_id")
    product = relationship("Product")
    uploader = relationship("User", foreign_keys=[uploaded_by])

class MediaUploadSession(Base, TenantMixin):
    """Tracks multipart upload sessions for large files."""
    __tablename__ = "media_upload_sessions"
    __table_args__ = ({"schema": "media"},)

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)

    entity_id = Column(Integer, nullable=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    chunk_size = Column(Integer, default=5 * 1024 * 1024)  # 5MB default
    total_chunks = Column(Integer, nullable=False)
    uploaded_chunks = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending | uploading | completed | failed
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)

    uploader = relationship("User", foreign_keys=[created_by])
