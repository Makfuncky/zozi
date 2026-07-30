"""
Media Management Service - Hierarchical Storage System
Implements organized storage for product images, videos, and supplier profiles
with support for country, supplier, and product hierarchies.

All media persists through the :class:`services.storage.StorageBackend` abstraction,
so the same code works with local disk (development) and S3-compatible object
storage behind a CDN (production).
"""

import mimetypes
import os
import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from models.media_models import MediaAsset
from services.storage import storage as _storage
from utils.file_validation import validate_upload_image, validate_upload_video, VIDEO_EXTENSIONS


def _build_storage_key(
    media_type: str,
    country_code: Optional[str] = None,
    supplier_id: Optional[int] = None,
    product_id: Optional[int] = None,
    variant_id: Optional[int] = None,
    subfolder: Optional[str] = None,
    filename: str = "",
) -> str:
    parts = [media_type]

    if country_code:
        parts.append(country_code.lower())
    if supplier_id:
        parts.append(f"supplier_{supplier_id}")
    if product_id:
        parts.append(f"product_{product_id}")
    if variant_id:
        parts.append(f"variant_{variant_id}")
    if subfolder:
        parts.append(subfolder)

    parts.append(filename)
    return "/".join(parts)


def generate_media_filename(
    file: UploadFile,
    entity_type: str,
    entity_id: Optional[int] = None,
) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    uuid_short = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename or "file")[1].lower()
    return f"{entity_type}_{entity_id or 'unknown'}_{timestamp}_{uuid_short}{ext}"


def save_product_media(
    file: UploadFile,
    db: Session,
    product_id: int,
    supplier_id: int,
    country_code: Optional[str] = None,
    variant_id: Optional[int] = None,
    is_main: bool = False,
) -> str:
    """Save product image/video with hierarchical path through the storage abstraction."""
    content = file.file.read()
    extension = os.path.splitext(file.filename or "")[1].lower()
    is_video = extension in VIDEO_EXTENSIONS or (file.content_type or "").startswith("video/")
    max_size = 25 * 1024 * 1024 if is_video else 10 * 1024 * 1024

    if len(content) > max_size:
        limit_mb = max_size // (1024 * 1024)
        media_label = "Video" if is_video else "Image"
        raise HTTPException(status_code=413, detail=f"{media_label} file exceeds {limit_mb}MB limit")

    validate_upload_video(content, file.filename or "") if is_video else validate_upload_image(content, file.filename or "")

    subfolder = "main" if is_main else "gallery"
    filename = generate_media_filename(file, "product", product_id)
    key = _build_storage_key(
        media_type="products",
        country_code=country_code,
        supplier_id=supplier_id,
        product_id=product_id,
        variant_id=variant_id,
        subfolder=subfolder,
        filename=filename,
    )

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    url = _storage.save(key, content, content_type=mime_type)

    if db is not None:
        try:
            asset = MediaAsset(
                country_code=country_code or "",
                supplier_id=supplier_id,
                product_id=product_id if product_id else None,
                entity_type="product",
                entity_id=product_id,
                variant="main" if is_main else "gallery",
                file_path=key,
                file_url=url,
                file_size_bytes=len(content),
                mime_type=mime_type,
                is_primary=is_main,
                uploaded_by=supplier_id,
            )
            db.add(asset)
            db.commit()
        except Exception as exc:
            db.rollback()

    return url


def save_supplier_media(
    file: UploadFile,
    db: Session,
    supplier_id: int,
    country_code: Optional[str] = None,
    media_type: str = "profile",
) -> str:
    """Save supplier profile image with hierarchical path through the storage abstraction."""
    content = file.file.read()
    extension = os.path.splitext(file.filename or "")[1].lower()
    is_video = extension in VIDEO_EXTENSIONS or (file.content_type or "").startswith("video/")
    max_size = 25 * 1024 * 1024 if is_video else 10 * 1024 * 1024

    if len(content) > max_size:
        limit_mb = max_size // (1024 * 1024)
        media_label = "Video" if is_video else "Image"
        raise HTTPException(status_code=413, detail=f"{media_label} file exceeds {limit_mb}MB limit")

    validate_upload_video(content, file.filename or "") if is_video else validate_upload_image(content, file.filename or "")

    filename = generate_media_filename(file, "supplier", supplier_id)
    key = _build_storage_key(
        media_type="suppliers",
        country_code=country_code,
        supplier_id=supplier_id,
        subfolder=media_type,
        filename=filename,
    )

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    url = _storage.save(key, content, content_type=mime_type)

    if db is not None:
        try:
            asset = MediaAsset(
                country_code=country_code or "",
                supplier_id=supplier_id,
                entity_type="supplier",
                entity_id=supplier_id,
                variant=media_type,
                file_path=key,
                file_url=url,
                file_size_bytes=len(content),
                mime_type=mime_type,
                is_primary=True,
                uploaded_by=supplier_id,
            )
            db.add(asset)
            db.commit()
        except Exception as exc:
            db.rollback()

    return url


def get_product_media_path(
    product_id: int,
    supplier_id: int,
    country_code: Optional[str] = None,
    is_main: bool = True,
    thumbnail: bool = False,
) -> str:
    subfolder = "thumbnails" if thumbnail else ("main" if is_main else "gallery")
    key = _build_storage_key(
        media_type="products",
        country_code=country_code,
        supplier_id=supplier_id,
        product_id=product_id,
        subfolder=subfolder,
    )
    return _storage.url(key.rstrip("/") + "/")


def generate_thumbnail_path(original_path: str, size: str = "small") -> str:
    path = Path(original_path)
    parent = str(path.parent)
    stem = path.stem
    suffix = path.suffix
    return f"{parent}/{stem}_{size}{suffix}"

