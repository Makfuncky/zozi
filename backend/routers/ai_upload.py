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

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from controllers.admin_controller import require_roles
from models import AIUploadJob, AIStagingProduct, AIStagingVariant, AIGenerationLog, Product, ProductVariant, User
from utils.variant_key import compute_variant_key
from utils.config import BASE_DIR

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


def _enrich_one(img_bytes: bytes, idx: int, job: AIUploadJob, image_url: str) -> tuple[AIStagingProduct, list[AIStagingVariant], list[AIGenerationLog]]:
    """Run AI enrichment for a single image. Returns staging product, its variants, and logs."""
    from services import ai_service

    name = ai_service.infer_product_name(image_bytes=img_bytes) or f"Untitled Product {idx + 1}"
    category = ai_service.suggest_category(name=name, image_bytes=img_bytes)
    tags = ai_service.suggest_tags(name=name, category=category)
    description = ai_service.generate_product_description(name=name, category=category, image_bytes=img_bytes)
    color = ai_service.detect_dominant_color(img_bytes)
    variant_template = ai_service.suggest_variant_template(name, category, tags=tags)
    sizes = ai_service.suggest_variant_options(name, category, tags=tags)
    materials = ai_service.suggest_material_candidates(name, category=category)

    confidence_score = None
    requires_review = (category == "General") or ai_service.is_generic_product_name(name)

    logs: list[AIGenerationLog] = []
    for field in ("name", "category", "tags", "description", "color"):
        logs.append(AIGenerationLog(
            job_id=job.id,
            field=field,
            model_used=ai_service.HF_API_TOKEN and "huggingface-inference" or "rule-based-fallback",
            prompt_hash=None,
            tokens_used=None,
            cost=None,
            confidence=None,
            country_code=job.country_code,
        ))

    staging = AIStagingProduct(
        job_id=job.id,
        name=name,
        description=description,
        price=None,
        stock=0,
        category=category,
        subcategory=None,
        color=color,
        brand=None,
        tags=tags,
        sizes=sizes,
        materials=materials,
        image_url=image_url,
        ai_description=description,
        variant_axes={"size": sizes, "color": [color] if color else [], "material": materials},
        attributes=None,
        confidence_score=confidence_score,
        requires_human_review=requires_review,
        country_code=job.country_code,
    )

    variants: list[AIStagingVariant] = []
    # Represent the detected color as a variant. If a size template exists, expand
    # one variant per size so the supplier can stock each combination.
    color_list = [color] if color else [None]
    for size in (sizes or [None]):
        for c in color_list:
            variants.append(AIStagingVariant(
                job_id=job.id,
                staging_product_id=0,  # set after staging flush
                variant_key=None,
                size=size,
                color=c,
                material=(materials or [None])[0] if materials else None,
                pattern=None,
                gender=None,
                sku=None,
                barcode=None,
                product_code=None,
                price=None,
                stock=0,
                media_url=image_url,
                attributes_json=None,
                is_active=True,
                confidence_score=confidence_score,
                requires_human_review=requires_review,
                country_code=job.country_code,
            ))
    return staging, variants, logs


def process_ai_upload_job(job_id: int) -> None:
    """Worker: enrich a job's media and write staging rows. Runs in a worker thread."""
    from db.database import get_db_context

    with get_db_context() as db:
        job = db.get(AIUploadJob, job_id)
        if job is None:
            logger.warning("AI upload job %s not found", job_id)
            return
        if job.status not in ("pending", "failed"):
            logger.info("AI upload job %s already processed (status=%s)", job_id, job.status)
            return

        job.status = "processing"
        db.commit()

        media_list = []
        try:
            parsed = json.loads(job.source_media_json or "[]")
        except (json.JSONDecodeError, TypeError):
            parsed = []

        staging_products: list[AIStagingProduct] = []
        try:
            for idx, media in enumerate(parsed):
                image_bytes_str = media.get("content") or media.get("bytes")
                image_url = media.get("url", "")
                if image_bytes_str:
                    img_bytes = bytes(image_bytes_str) if isinstance(image_bytes_str, str) else image_bytes_str
                elif media.get("key"):
                    from services.storage import storage as _storage
                    img_bytes = _storage.read(media["key"])
                else:
                    continue
                try:
                    staging, variants, logs = _enrich_one(img_bytes, idx, job, image_url)
                except Exception as exc:  # per-image isolation
                    logger.warning("AI enrichment failed for image %s in job %s: %s", image_url, job_id, exc)
                    db.add(AIGenerationLog(
                        job_id=job.id, field="error", model_used="worker",
                        prompt_hash=None, tokens_used=None, cost=None, confidence=None,
                        country_code=job.country_code,
                    ))
                    continue
                db.add(staging)
                db.flush()  # assign staging.id
                for v in variants:
                    v.staging_product_id = staging.id
                    v.variant_key = f"staged-{uuid.uuid4().hex}"
                    db.add(v)
                for log in logs:
                    db.add(log)
                staging_products.append(staging)
                media_list.append({"path": image_url, "staging_id": staging.id})

            job.source_media_json = json.dumps(media_list)
            if staging_products:
                job.status = "staged"
            else:
                job.status = "failed"
                job.error_log = "No images could be enriched."
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(AIUploadJob, job_id)
            if job:
                job.status = "failed"
                job.error_log = str(exc)[:2000]
                db.commit()
            logger.exception("AI upload job %s failed: %s", job_id, exc)


def _publish_staging(db: Session, staging: AIStagingProduct, overrides: Optional[dict], job: AIUploadJob) -> Product:
    name = (overrides or {}).get("name") or staging.name
    description = (overrides or {}).get("description") or staging.description
    category = (overrides or {}).get("category") or staging.category
    price = (overrides or {}).get("price") or staging.price or 0
    color = (overrides or {}).get("color") or staging.color
    brand = (overrides or {}).get("brand") or staging.brand

    slug = f"{_slugify(name) or 'product'}-{uuid.uuid4().hex[:8]}"
    product = Product(
        name=name,
        slug=slug,
        description=description,
        ai_description=staging.ai_description,
        price=price,
        stock=0,
        category=category,
        subcategory=staging.subcategory,
        color=color,
        brand=brand,
        tags=staging.tags,
        materials=staging.materials,
        sizes=staging.sizes,
        image_url=staging.image_url,
        images=[staging.image_url] if staging.image_url else None,
        supplier_id=job.supplier_id,
        country_code=job.country_code,
        is_active=True,
        is_verified=True,
        moderation_status="approved",
        variant_axes=staging.variant_axes,
    )
    db.add(product)
    db.flush()

    variants = db.query(AIStagingVariant).filter(AIStagingVariant.staging_product_id == staging.id).all()
    total_stock = 0
    for sv in variants:
        v_overrides = (overrides or {}).get("variants", {}).get(str(sv.id)) or {}
        v_color = v_overrides.get("color", sv.color)
        v_size = v_overrides.get("size", sv.size)
        v_price = v_overrides.get("price", sv.price) or price
        v_stock = int(v_overrides.get("stock", sv.stock) or 0)
        total_stock += v_stock
        variant = ProductVariant(
            product_id=product.id,
            size=v_size,
            color=v_color,
            material=sv.material,
            pattern=sv.pattern,
            gender=sv.gender,
            sku=sv.sku,
            barcode=sv.barcode,
            product_code=sv.product_code,
            price=v_price,
            stock=v_stock,
            media_url=sv.media_url,
            attributes_json=sv.attributes_json,
            is_active=True,
            country_code=job.country_code,
            variant_key=compute_variant_key(product.id, v_size, v_color, sv.material, sv.pattern, sv.gender),
        )
        db.add(variant)

    product.stock = total_stock
    return product


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


@router.get("/jobs/{job_id}")
def get_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
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


@router.post("/jobs/{job_id}/publish", status_code=200)
def publish_ai_upload_job(
    job_id: int,
    overrides: Optional[dict] = None,
    current_user: dict = _AUTH,
    db: Session = Depends(get_db),
):
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


@router.post("/jobs/{job_id}/cancel", status_code=200)
def cancel_ai_upload_job(job_id: int, current_user: dict = _AUTH, db: Session = Depends(get_db)):
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status in ("completed",):
        raise HTTPException(status_code=409, detail="Job already completed.")
    job.status = "cancelled"
    db.commit()
    return {"job_id": job.id, "status": "cancelled"}

