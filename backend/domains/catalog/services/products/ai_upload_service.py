"""AI upload pipeline write service.

Owns every DB mutation of the AI upload flow:

    * ``create_ai_upload_job``   — persist a new job + its uploaded media
    * ``run_ai_upload_job``      — worker body: enrich media -> staging rows
    * ``process_ai_upload_job``  — worker entrypoint (opens its own session)
    * ``publish_ai_upload_job``  — promote staging rows to products/variants
    * ``cancel_ai_upload_job``   — mark a job cancelled
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.catalog.ports import Product
from domains.catalog.ports import ProductVariant
from domains.catalog.models.ai_upload import AIGenerationLog
from domains.catalog.models.ai_upload import AIStagingProduct
from domains.catalog.models.ai_upload import AIStagingVariant
from domains.catalog.models.ai_upload import AIUploadJob
from infrastructure.storage.storage import get_storage
from providers.image.free_image_tools import (
    magic_erase, smart_crop, auto_rotate, auto_lighting,
)
from providers.image import HAS_CV2
from providers.bg_removal import remove_background as bg_remove
from infrastructure.utils.variant_key import compute_variant_key

logger = logging.getLogger(__name__)


def _preprocess_for_ai(img_bytes: bytes) -> bytes:
    """Preprocess supplier-uploaded image before AI inference."""
    if not HAS_CV2:
        return img_bytes
    img_bytes = auto_rotate(img_bytes)
    img_bytes = auto_lighting(img_bytes)
    img_bytes = smart_crop(img_bytes, target_ratio=1.0)
    img_bytes = magic_erase(img_bytes, max_dim=1024)
    try:
        img_bytes = bg_remove(img_bytes, fast_mode=True)
    except Exception as exc:
        logger.warning("Background removal failed, using original: %s", exc)
    return img_bytes


def _slugify(name: str) -> str:
    slug = (name or "").strip().lower()
    slug = "".join(ch if ch.isalnum() or ch in (" ", "-") else "-" for ch in slug)
    slug = slug.replace(" ", "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "item"


def create_ai_upload_job(
    db: Session,
    *,
    supplier_id: int,
    uploaded_files: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> AIUploadJob:
    job = AIUploadJob(
        supplier_id=supplier_id,
        status="pending",
        uploaded_files=json.dumps(uploaded_files or []),
        meta=json.dumps(metadata or {}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_ai_upload_job(db: Session, job_id: int) -> dict[str, Any]:
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise ValueError("Job not found.")
    if job.status not in ("pending",):
        raise ValueError(f"Job in status {job.status} cannot be run.")
    job.status = "processing"
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": job.status}


def process_ai_upload_job(job_id: int) -> dict[str, Any]:
    """Worker entrypoint: opens its own session and dispatches the work."""
    from infrastructure.database.database import SessionLocal
    with SessionLocal() as db:
        return run_ai_upload_job(db, job_id)


def publish_ai_upload_job(db: Session, job_id: int) -> dict[str, Any]:
    """Promote staging rows to live product/variant records."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise ValueError("Job not found.")
    if job.status not in ("processing", "completed"):
        raise ValueError(f"Job in status {job.status} cannot be published.")
    staging = (
        db.query(AIStagingProduct)
        .filter(AIStagingProduct.job_id == job_id)
        .all()
    )
    # Batch-load all variants outside the loop to avoid N+1 queries
    staging_ids = [row.id for row in staging]
    variants_by_product: dict[int, list[AIStagingVariant]] = {}
    if staging_ids:
        all_variants = (
            db.query(AIStagingVariant)
            .filter(AIStagingVariant.staging_product_id.in_(staging_ids))
            .all()
        )
        for v in all_variants:
            variants_by_product.setdefault(v.staging_product_id, []).append(v)

    promoted = 0
    for row in staging:
        product = Product(
            name=row.name,
            slug=_slugify(row.name),
            description=row.description or "",
            price=row.price or 0,
            category=row.category or "general",
            image_url=row.image_url,
            supplier_id=job.supplier_id,
            is_active=True,
        )
        db.add(product)
        db.flush()
        for v in variants_by_product.get(row.id, []):
            db.add(ProductVariant(
                product_id=product.id,
                sku=v.sku,
                price=v.price or product.price,
                stock=v.stock or 0,
                attributes=json.dumps(v.attributes or {}),
                variant_key=compute_variant_key(v.attributes or {}),
            ))
        promoted += 1
    job.status = "completed"
    db.commit()
    return {"job_id": job.id, "promoted": promoted}


def cancel_ai_upload_job(db: Session, job_id: int) -> dict[str, Any]:
    """Mark a job cancelled."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise ValueError("Job not found.")
    if job.status in ("completed",):
        raise ValueError("Job already completed.")
    job.status = "cancelled"
    db.commit()
    return {"job_id": job.id, "status": "cancelled"}
