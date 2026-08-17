"""Auto-migrated service logic from routers/system_ai_upload.py."""
from __future__ import annotations

from __future__ import annotations
from services.system.system_ai_upload_service import _enrich_one, _slugify, _save_upload, _publish_staging
from services.system.system_ai_upload_service import process_ai_upload_job

import json

import logging

import os

import uuid

from typing import Optional

from fastapi import BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from modules.admin.routers.auth import require_roles
from models import AIUploadJob, AIStagingProduct, AIStagingVariant, AIGenerationLog, Product, ProductVariant, User

from infrastructure.utils.variant_key import compute_variant_key

from infrastructure.utils.config import BASE_DIR

logger = logging.getLogger(__name__)

_AUTH = Depends(require_roles("supplier", "admin"))






async def create_ai_upload_job(background_tasks: BackgroundTasks, images: list[UploadFile], country_code: str, model_used: Optional[str], prompt_hash: Optional[str], current_user: dict, db: Session):
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required.")

    user_id = current_user.get("id") or current_user.get("user_id")
    if user_id is None and isinstance(current_user.get("user"), dict):
        user_id = current_user["user"].get("id")

    job = AIUploadJob(
        supplier_id=int(user_id),
        status="pending",
        model_used=model_used,
        prompt_hash=prompt_hash,
        source_media_json="[]",
        country_code=country_code,
    )
    db.add(job)
    db.flush()

    media_list = []
    for img in images:
        try:
            key, url, content = _save_upload(img, str(job.id))
            media_list.append({"filename": img.filename, "key": key, "url": url})
        except Exception as exc:
            logger.warning("Failed to save upload %s: %s", img.filename, exc)
    job.source_media_json = json.dumps(media_list)

    if not media_list:
        raise HTTPException(status_code=422, detail="No images could be saved.")

    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_ai_upload_job, job.id)
    return {
        "job_id": job.id,
        "status": job.status,
        "country_code": job.country_code,
        "media_count": len(media_list),
    }

def get_ai_upload_job(job_id: int, current_user: dict, db: Session):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    staging = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    logs = db.query(AIGenerationLog).filter(AIGenerationLog.job_id == job_id).all()
    return {
        "job": {
            "id": job.id,
            "status": job.status,
            "model_used": job.model_used,
            "tokens_used": float(job.tokens_used) if job.tokens_used is not None else None,
            "error_log": job.error_log,
            "country_code": job.country_code,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "created_product_id": job.created_product_id,
        },
        "staging_products": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "color": s.color,
                "brand": s.brand,
                "price": float(s.price) if s.price is not None else None,
                "tags": s.tags,
                "sizes": s.sizes,
                "materials": s.materials,
                "image_url": s.image_url,
                "confidence_score": float(s.confidence_score) if s.confidence_score is not None else None,
                "requires_human_review": s.requires_human_review,
            }
            for s in staging
        ],
        "logs": [{"field": lg.field, "model_used": lg.model_used, "confidence": float(lg.confidence) if lg.confidence is not None else None} for lg in logs],
    }

def publish_ai_upload_job(job_id: int, overrides: Optional[dict], current_user: dict, db: Session):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status not in ("staged", "failed"):
        raise HTTPException(status_code=409, detail=f"Job is not ready to publish (status={job.status}).")

    staging_products = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    if not staging_products:
        raise HTTPException(status_code=409, detail="No staging products to publish.")

    created_ids = []
    for staging in staging_products:
        so = (overrides or {}).get(str(staging.id)) if isinstance(overrides, dict) else None
        product = _publish_staging(db, staging, so, job)
        created_ids.append(product.id)
        if job.created_product_id is None:
            job.created_product_id = product.id

    job.status = "completed"
    db.commit()
    return {"job_id": job.id, "status": "completed", "created_product_ids": created_ids}

def cancel_ai_upload_job(job_id: int, current_user: dict, db: Session):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status in ("completed",):
        raise HTTPException(status_code=409, detail="Job already completed.")
    job.status = "cancelled"
    db.commit()
    return {"job_id": job.id, "status": "cancelled"}


