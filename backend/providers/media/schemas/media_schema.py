from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class MediaAssetSchema(BaseModel):
    id: int
    storage_key: str
    url: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    country_code: Optional[str] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


class UploadSessionSchema(BaseModel):
    id: int
    upload_token: str
    status: str
    country_code: Optional[str] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


__all__ = ["MediaAssetSchema", "UploadSessionSchema"]
