"""Customer reviews router — thin per-actor router for review photo uploads.

Per ARCHITECTURE_STACK.md §3, routers are thin:
auth context + require_feature(...) + one service call.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customer/reviews", tags=["customer", "reviews"])

# Allowed image MIME types for review photos
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
# Max upload size: 5 MB
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def _store_upload(file: UploadFile, review_id: int) -> str:
    """Store an uploaded review photo and return the public URL."""
    from infrastructure.storage.storage import storage as _store

    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {file.content_type}. "
                   f"Allowed: {', '.join(sorted(_ALLOWED_IMAGE_TYPES))}",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        ext = "jpg"

    key = f"review_photos/{review_id}/{uuid.uuid4().hex}.{ext}"

    chunk = file.file.read(_MAX_UPLOAD_BYTES + 1)
    if len(chunk) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {_MAX_UPLOAD_BYTES // 1024 // 1024} MB limit",
        )

    content_type = file.content_type or "image/jpeg"
    url = _store.save(key, chunk, content_type=content_type)
    return url


@router.post("/{id}/photos", status_code=status.HTTP_200_OK)
def upload_review_photo(
    id: int,
    file: UploadFile = File(..., description="Review photo (JPEG/PNG/WebP, max 5 MB)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("catalog.review.create")),
):
    """Upload a photo attachment for an existing review."""
    from domains.catalog.ports import Review
    from domains.customers.services.reviews_service import update_review

    review = db.query(Review).filter(
        Review.id == id,
        Review.is_deleted.is_(False),
    ).first()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    user_id = int(current_user.get("id", 0))
    user_role = current_user.get("role", "customer")
    if review.user_id != user_id and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to modify this review",
        )

    url = _store_upload(file, review_id=id)
    updated = update_review(db, review=review, updates={"image_url": url})
    return {
        "id": updated.id,
        "image_url": updated.image_url,
        "detail": "Review photo uploaded",
    }
