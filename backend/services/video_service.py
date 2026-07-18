from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from models import Product, ProductVideo, VideoAnalytics
from services.media_service import save_product_media, get_media_base_path

logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_VIDEO_SIZE_MB = 100
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024


class VideoService:
    def __init__(self, db: Session):
        self.db = db

    def upload_video(
        self,
        video: UploadFile,
        product_id: int,
        supplier_id: int,
        video_type: str = "product_demo",
        title: Optional[str] = None,
        description: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        content = video.file.read()
        filename = video.filename or ""
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_VIDEO_EXTENSIONS and not (video.content_type or "").startswith("video/"):
            raise HTTPException(status_code=400, detail="Unsupported video format")

        if len(content) > MAX_VIDEO_SIZE_BYTES:
            raise HTTPException(status_code=400, detail=f"Video size must be less than {MAX_VIDEO_SIZE_MB}MB")

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.supplier_id != supplier_id:
            raise HTTPException(status_code=403, detail="Not authorized to upload video for this product")

        storage_path = save_product_media(
            file=video,
            db=self.db,
            product_id=product_id,
            supplier_id=supplier_id,
            country_code=country_code,
            is_main=False,
        )

        base_url = "/uploads"
        video_url = f"{base_url}/{storage_path}"

        video_record = ProductVideo(
            product_id=product_id,
            video_url=video_url,
            video_type=video_type,
            title=title or filename,
            description=description,
            upload_status="ready",
        )

        self.db.add(video_record)
        self.db.flush()

        product.video_count = (product.video_count or 0) + 1
        self.db.commit()
        self.db.refresh(video_record)

        return self._video_to_dict(video_record)

    def get_product_videos(self, product_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        videos = (
            self.db.query(ProductVideo)
            .filter(
                ProductVideo.product_id == product_id,
                ProductVideo.upload_status == "ready",
            )
            .order_by(ProductVideo.is_featured.desc(), ProductVideo.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._video_to_dict(v) for v in videos]

    def get_recommended_videos(self, product_id: int, limit: int = 8) -> List[Dict[str, Any]]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []

        query = (
            self.db.query(ProductVideo)
            .join(Product, ProductVideo.product_id == Product.id)
            .filter(
                ProductVideo.id != product_id,
                ProductVideo.upload_status == "ready",
                Product.is_deleted == False,
                Product.is_active == True,
                Product.is_approved == True,
            )
        )

        if product.category_id:
            query = query.filter(Product.category_id == product.category_id)

        if product.brand:
            query = query.filter(Product.brand == product.brand)

        videos = query.order_by(ProductVideo.views_count.desc(), ProductVideo.created_at.desc()).limit(limit).all()

        return [self._video_to_dict(v) for v in videos]

    def get_featured_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        videos = (
            self.db.query(ProductVideo)
            .filter(
                ProductVideo.upload_status == "ready",
                ProductVideo.is_featured == True,
            )
            .order_by(ProductVideo.views_count.desc(), ProductVideo.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._video_to_dict(v) for v in videos]

    def track_event(
        self,
        video_id: int,
        event_type: str,
        user_id: Optional[int] = None,
        watch_duration: Optional[int] = None,
        device_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        video = self.db.query(ProductVideo).filter(ProductVideo.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        analytics = VideoAnalytics(
            video_id=video_id,
            user_id=user_id,
            event_type=event_type,
            watch_duration_seconds=watch_duration,
            device_type=device_type,
        )
        self.db.add(analytics)

        if event_type == "view":
            video.views_count = (video.views_count or 0) + 1

        self.db.commit()
        return {"status": "tracked", "video_id": video_id, "event_type": event_type}

    def _video_to_dict(self, video: ProductVideo) -> Dict[str, Any]:
        return {
            "id": video.id,
            "product_id": video.product_id,
            "video_url": video.video_url,
            "thumbnail_url": video.thumbnail_url,
            "duration_seconds": video.duration_seconds,
            "video_type": video.video_type,
            "title": video.title,
            "description": video.description,
            "views_count": video.views_count,
            "is_featured": video.is_featured,
            "upload_status": video.upload_status,
            "created_at": video.created_at.isoformat() if video.created_at else None,
            "product_name": video.product.name if video.product else None,
            "product_price": float(video.product.price) if video.product and video.product.price else None,
        }

