"""AI upload pipeline router (Phase 4).

Replaces the old inline AI enrichment loop in ``controllers/supplier_controller.py``
with a durable, resumable, audited flow:

    POST /ai-upload/jobs            -> create job (pending) + schedule worker
    GET  /ai-upload/jobs/{id}       -> inspect job + staging + logs
    POST /ai-upload/jobs/{id}/publish -> commit reviewed staging -> products/variants
    POST /ai-upload/jobs/{id}/cancel  -> mark job cancelled

The worker (``process_ai_upload_job``) runs outside the request context (RLS
restricted flag is False, so it can read/write across the job's country) and:

    1. saves uploaded media to ``uploads/ai_upload/<job_id>/``
    2. calls ``services.ai_service`` to enrich each image (category/tags/description/
       color/variant template) — falls back to rule-based results if the HF token
       is absent
    3. writes ``ai_staging_products`` / ``ai_staging_variants`` (+ ``ai_generation_logs``)
    4. marks the job ``staged`` (awaiting human review) or ``failed``

The supplier reviews the staging (front-end) and publishes, which upserts into
``products`` / ``product_variants`` using the deterministic ``variant_key`` so
re-runs are idempotent.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from data.db import get_db
from utils.dependencies import require_roles

from services.media.media_router_service import (
    get_ai_upload_job as get_ai_upload_job_service,
    create_ai_upload_job as create_ai_upload_job_service,
    publish_ai_upload_job as publish_ai_upload_job_service,
    cancel_ai_upload_job as cancel_ai_upload_job_service,
    process_ai_upload_job,
)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-upload"])

_AUTH = Depends(require_roles("supplier", "admin"))


def _slugify(name: str) -> str:
    slug = (name or "").strip().lower()
    slug = "".join(ch if ch.isalnum() or ch in (" ", "-") else "-" for ch in slug)
    slug = slug.replace(" ", "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:60]


def _save_upload(file: UploadFile, job_dir: str) -> tuple[str, str, bytes]:
    """Save uploaded file through storage abstraction.

    Returns ``(storage_key, public_url, content_bytes)``.
    """
    from services.storage import storage as _storage

    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    key = f"ai_upload/{os.path.basename(job_dir)}/{fname}"
    content = file.file.read()
    mime_type = file.content_type or "application/octet-stream"
    url = _storage.save(key, content, content_type=mime_type)
    return key, url, content


@router.post("/jobs", status_code=201)
async def create_ai_upload_job(
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(default=[]),
    country_code: str = Form(...),
    model_used: Optional[str] = Form(None),
    prompt_hash: Optional[str] = Form(None),
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    """Create an AI upload job."""
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required.")

    user_id = current_user.get("id") or current_user.get("user_id")
    if user_id is None and isinstance(current_user.get("user"), dict):
        user_id = current_user["user"].get("id")

    media_list = []
    for img in images:
        try:
            key, url, content = _save_upload(img, str(uuid.uuid4().hex))
            media_list.append({"filename": img.filename, "key": key, "url": url})
        except Exception as exc:
            logger.warning("Failed to save upload %s: %s", img.filename, exc)

    try:
        result = create_ai_upload_job_service(
            db=db,
            supplier_id=int(user_id),
            images_data=media_list,
            country_code=country_code,
            model_used=model_used,
            prompt_hash=prompt_hash,
        )
    except Exception as e:
        if "No images could be saved" in str(e):
            raise HTTPException(status_code=422, detail="No images could be saved.")
        raise

    background_tasks.add_task(process_ai_upload_job, result["job_id"])
    return result


@router.get("/jobs/{job_id}")
def get_ai_upload_job(
    job_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    """Get an AI upload job with staging products and logs."""
    try:
        return get_ai_upload_job_service(db=db, job_id=job_id, skip=skip, limit=limit)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Job not found.")
        raise


@router.post("/jobs/{job_id}/publish", status_code=200)
def publish_ai_upload_job(
    job_id: int,
    overrides: Optional[dict] = None,
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    """Publish an AI upload job's staging products."""
    try:
        return publish_ai_upload_job_service(db=db, job_id=job_id, overrides=overrides)
    except Exception as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="Job not found.")
        if "not ready to publish" in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        if "No staging products" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(500, detail=f"Publish failed: {msg}")


@router.post("/jobs/{job_id}/cancel", status_code=200)
def cancel_ai_upload_job(
    job_id: int,
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
    """Cancel an AI upload job."""
    try:
        return cancel_ai_upload_job_service(db=db, job_id=job_id)
    except Exception as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail="Job not found.")
        if "already completed" in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(500, detail=str(e))
