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
from providers.ai.image_similarity import compute_image_embedding, find_similar_images
from providers.bg_removal import remove_background as bg_remove
from infrastructure.utils.variant_key import compute_variant_key
import structlog
logger = structlog.get_logger(__name__)

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
    return slug.strip("-")[:60]


def _save_upload(file: Any, job_dir: str) -> tuple[str, str, bytes]:
    storage = get_storage()
    ext = os.path.splitext(getattr(file, "filename", "") or "")[1] or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    key = f"ai_upload/{os.path.basename(job_dir)}/{fname}"
    content = file.file.read()
    mime_type = getattr(file, "content_type", None) or "application/octet-stream"
    url = storage.save(key, content, content_type=mime_type)
    return key, url, content


def _enrich_one(
    img_bytes: bytes,
    idx: int,
    job: AIUploadJob,
    image_url: str,
) -> tuple[AIStagingProduct, list[AIStagingVariant], list[AIGenerationLog]]:
    from providers.ai.ai_service import ai_service

    img_bytes = _preprocess_for_ai(img_bytes)
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
    color_list = [color] if color else [None]
    for size in (sizes or [None]):
        for c in color_list:
            variants.append(AIStagingVariant(
                job_id=job.id,
                staging_product_id=0,
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


def create_ai_upload_job(
    db: Session,
    *,
    supplier_id: int,
    country_code: str,
    images: list[Any],
    model_used: Optional[str] = None,
    prompt_hash: Optional[str] = None,
) -> dict[str, Any]:
    """Persist a new AI upload job together with its uploaded media."""
    if not images:
        raise ValueError("At least one image is required.")

    job = AIUploadJob(
        supplier_id=int(supplier_id),
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
            media_list.append({"filename": getattr(img, "filename", None), "key": key, "url": url})
        except Exception as exc:
            logger.warning("Failed to save upload %s: %s", getattr(img, "filename", None), exc)
    job.source_media_json = json.dumps(media_list)

    if not media_list:
        raise ValueError("No images could be saved.")

    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "status": job.status,
        "country_code": job.country_code,
        "media_count": len(media_list),
    }


def run_ai_upload_job(db: Session, job_id: int) -> None:
    """Worker body: enrich a job's media and write staging rows."""
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
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse source_media_json for job %s: %s", job.id, exc)
        parsed = []

    staging_products: list[AIStagingProduct] = []
    try:
        for idx, media in enumerate(parsed):
            image_bytes_str = media.get("content") or media.get("bytes")
            image_url = media.get("url", "")
            if image_bytes_str:
                img_bytes = bytes(image_bytes_str) if isinstance(image_bytes_str, str) else image_bytes_str
            elif media.get("key"):
                storage = get_storage()
                img_bytes = storage.read(media["key"])
            else:
                continue
            try:
                staging, variants, logs = _enrich_one(img_bytes, idx, job, image_url)
            except Exception as exc:
                logger.warning("AI enrichment failed for image %s in job %s: %s", image_url, job_id, exc)
                db.add(AIGenerationLog(
                    job_id=job.id, field="error", model_used="worker",
                    prompt_hash=None, tokens_used=None, cost=None, confidence=None,
                    country_code=job.country_code,
                ))
                continue
            db.add(staging)
            db.flush()
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


def process_ai_upload_job(job_id: int) -> None:
    """Worker entrypoint: opens its own session and runs the enrichment pass."""
    from infrastructure.database.database import get_db_context

    with get_db_context() as db:
        run_ai_upload_job(db, job_id)


def publish_ai_upload_job(
    db: Session,
    job_id: int,
    overrides: Optional[dict] = None,
) -> dict[str, Any]:
    """Promote a job's reviewed staging rows into products/variants."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise ValueError("Job not found.")
    if job.status not in ("staged", "failed"):
        raise ValueError(f"Job is not ready to publish (status={job.status}).")

    staging_products = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    if not staging_products:
        raise ValueError("No staging products to publish.")

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


def _check_duplicate_image(img_bytes: bytes, existing_products: list[dict]) -> list[dict]:
    """Find visually similar products."""
    try:
        return find_similar_images(img_bytes, existing_products, limit=5)
    except Exception as exc:
        logger.warning("Duplicate image check failed: %s", exc)
        return []
