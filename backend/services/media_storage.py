"""Media storage service for handling uploads, processing, and CDN integration."""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from models import MediaAsset, MediaUploadSession
from utils.config import settings


class MediaStorageService:
    """Handles media storage with 3-tier path structure and variant generation."""
    
    STORAGE_BASE = settings.media_storage_base or "/uploads/media"
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_storage_path(
        self,
        country_code: str,
        supplier_id: Optional[int],
        product_id: Optional[int],
        variant: str,
        filename: str,
    ) -> str:
        """Generate 3-tier storage path: /{country}/{supplier}/{product}/variant_filename"""
        ext = os.path.splitext(filename)[1].lower()
        
        parts = [self.STORAGE_BASE, country_code.upper()]
        if supplier_id:
            parts.append(str(supplier_id))
        else:
            parts.append("system")
        
        if product_id:
            parts.append(str(product_id))
        else:
            parts.append("general")
        
        parts.append(f"{variant}_{uuid.uuid4().hex[:12]}{ext}")
        return os.path.join(*parts)
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def create_upload_session(
        self,
        country_code: str,
        entity_type: str,
        entity_id: Optional[int],
        filename: str,
        file_size: int,
        mime_type: str,
        uploaded_by: Optional[int],
    ) -> MediaUploadSession:
        """Create a new multipart upload session."""
        session = MediaUploadSession(
            session_id=uuid.uuid4().hex,
            country_code=country_code,
            entity_type=entity_type,
            entity_id=entity_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            total_chunks=(file_size + 5*1024*1024 - 1) // (5*1024*1024),
            created_by=uploaded_by,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def complete_upload_session(
        self,
        session_id: str,
        storage_path: str,
        file_url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> MediaAsset:
        """Complete upload and create media asset record."""
        session = self.db.query(MediaUploadSession).filter_by(session_id=session_id).first()
        if not session:
            raise ValueError(f"Upload session {session_id} not found")
        
        asset = MediaAsset(
            country_code=session.country_code,
            supplier_id=session.entity_id if session.entity_type == "supplier" else None,
            product_id=session.entity_id if session.entity_type == "product" else None,
            entity_type=session.entity_type,
            entity_id=session.entity_id,
            variant="original",
            file_path=storage_path,
            file_url=file_url,
            file_size_bytes=session.file_size,
            mime_type=session.mime_type,
            width=width,
            height=height,
            uploaded_by=session.created_by,
        )
        self.db.add(asset)
        
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(asset)
        return asset
    
    def generate_variants(self, original_asset: MediaAsset) -> list[MediaAsset]:
        """Generate thumbnail and other variants for an image."""
        variants = ["thumbnail", "small", "gallery"]
        created = []
        
        for variant in variants:
            variant_path = self._generate_storage_path(
                original_asset.country_code,
                original_asset.supplier_id,
                original_asset.product_id,
                variant,
                original_asset.file_path,
            )
            variant_asset = MediaAsset(
                country_code=original_asset.country_code,
                supplier_id=original_asset.supplier_id,
                product_id=original_asset.product_id,
                entity_type=original_asset.entity_type,
                entity_id=original_asset.entity_id,
                variant=variant,
                file_path=variant_path,
                file_url=original_asset.file_url.replace("original", variant),
                file_size_bytes=original_asset.file_size_bytes,
                mime_type=original_asset.mime_type,
                width=original_asset.width,
                height=original_asset.height,
                uploaded_by=original_asset.uploaded_by,
            )
            self.db.add(variant_asset)
            created.append(variant_asset)
        
        self.db.commit()
        return created

