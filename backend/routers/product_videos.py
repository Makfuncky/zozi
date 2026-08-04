from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import User
from services.video_service import VideoService
from utils.dependencies import get_current_user

router = APIRouter(tags=["product-videos"])


@router.post("/upload")
async def upload_product_video(
    product_id: int = Form(...),
    video_type: str = Form("product_demo"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = VideoService(db)
    result = service.upload_video(
        video=video,
        product_id=product_id,
        supplier_id=current_user.id,
        video_type=video_type,
        title=title,
        description=description,
    )
    return result


@router.get("/product/{product_id}")
async def get_product_videos(
    product_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    service = VideoService(db)
    videos = service.get_product_videos(product_id=product_id, limit=limit)
    return {"videos": videos}


@router.get("/recommendations/{product_id}")
async def get_video_recommendations(
    product_id: int,
    limit: int = 8,
    db: Session = Depends(get_db),
):
    service = VideoService(db)
    recommendations = service.get_recommended_videos(product_id=product_id, limit=limit)
    return {"recommendations": recommendations}


@router.get("/featured")
async def get_featured_videos(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    service = VideoService(db)
    videos = service.get_featured_videos(limit=limit)
    return {"videos": videos}


@router.post("/{video_id}/track")
async def track_video_event(
    video_id: int,
    event_type: str,
    watch_duration: Optional[int] = None,
    device_type: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = VideoService(db)
    return service.track_event(
        video_id=video_id,
        event_type=event_type,
        user_id=current_user.id if current_user else None,
        watch_duration=watch_duration,
        device_type=device_type,
    )

