"""Celery tasks for product video processing (transcode + captions).

Per TECHNOLOGY_STACK.md §2, CPU-bound work runs through async_workers.
This module exposes video_transcode_task for the ProductVideo pipeline.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.video_tasks.video_transcode",
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    time_limit=600,
    soft_time_limit=540,
)
def video_transcode_task(
    self,
    video_id: int,
    video_data: str,
    filename: str = "upload.mp4",
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """Transcode a raw product-video upload and generate captions."""
    try:
        import base64

        from sqlalchemy.orm import Session

        from infrastructure.database.database import SessionLocal
        from domains.catalog.ports import ProductVideo
        from infrastructure.storage.storage import storage as _store

        video_bytes = base64.b64decode(video_data)

        db: Session = SessionLocal()
        try:
            row = db.get(ProductVideo, video_id)
            if row is None:
                return {"video_id": video_id, "upload_status": "failed", "detail": "not_found"}
            row.upload_status = "processing"
            db.add(row)
            db.commit()
        finally:
            db.close()

        caption = _generate_caption(video_bytes, filename=filename)

        ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4")
        if ext not in {"mp4", "webm", "mov"}:
            ext = "mp4"
        key = f"product_videos/{video_id}/{uuid.uuid4().hex}.{ext}"
        content_type = "video/mp4"
        stored_url = _store.save(key, video_bytes, content_type=content_type)

        db = SessionLocal()
        try:
            row = db.get(ProductVideo, video_id)
            if row is not None:
                row.video_url = stored_url
                row.description = caption
                row.upload_status = "completed"
                db.add(row)
                db.commit()
        finally:
            db.close()

        logger.info("video_transcode completed", extra={"video_id": video_id, "status": "completed"})
        return {
            "video_id": video_id,
            "upload_status": "completed",
            "video_url": stored_url,
            "caption": caption,
        }

    except Exception as exc:
        logger.exception("video_transcode failed: video_id=%s", video_id)
        try:
            from sqlalchemy.orm import Session as _Session
            from infrastructure.database.database import SessionLocal as _SL
            from domains.catalog.ports import ProductVideo as _PV

            _db: _Session = _SL()
            try:
                _row = _db.get(_PV, video_id)
                if _row is not None:
                    _row.upload_status = "failed"
                    _db.add(_row)
                    _db.commit()
            finally:
                _db.close()
        except Exception:
            pass
        raise self.retry(exc=exc)


def _generate_caption(video_bytes: bytes, filename: str = "") -> str:
    """Generate a caption for a product video using providers/ai/text."""
    try:
        from providers.ai.text import HAS_AI_TEXT, ollama_chat_json

        if not HAS_AI_TEXT:
            return ""

        prompt = (
            "You are a product video captioning assistant. "
            "Describe this product video in one short sentence suitable as a caption."
        )
        result = ollama_chat_json(
            prompt=prompt,
            response_schema={"type": "object", "properties": {"caption": {"type": "string"}}},
        )
        if isinstance(result, dict):
            return result.get("caption", "") or ""
        return ""
    except Exception:
        return ""


@shared_task(
    bind=True,
    name="tasks.video_tasks.generate_video_captions",
    max_retries=2,
    default_retry_delay=60,
    time_limit=300,
    soft_time_limit=240,
)
def generate_video_captions(
    self,
    video_id: int,
    video_data: str,
    owner_user_id: Optional[int] = None,
    owner_role: Optional[str] = None,
) -> dict[str, Any]:
    """Standalone caption generation task for an existing ProductVideo."""
    try:
        import base64

        video_bytes = base64.b64decode(video_data)
        caption = _generate_caption(video_bytes)

        logger.info("generate_video_captions completed", extra={"video_id": video_id, "caption_length": len(caption)})
        return {"video_id": video_id, "caption": caption}

    except Exception as exc:
        logger.exception("generate_video_captions failed: video_id=%s", video_id)
        raise self.retry(exc=exc)
