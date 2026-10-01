from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from . import Base

__all__ = ["MediaAsset", "UploadSession"]


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = {"schema": "media"}

    id = Column(Integer, primary_key=True, index=True)
    storage_key = Column(String(500), nullable=False, unique=True)
    url = Column(String(1000), nullable=False)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    __table_args__ = {"schema": "media"}

    id = Column(Integer, primary_key=True, index=True)
    upload_token = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="pending")
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
