"""Media router service module — orchestrates DB operations for upload routers."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from data.models import (
    AIStagingProduct,
    AIStagingVariant,
    AIUploadJob,
    AIGenerationLog,
    Product,
    ProductVariant,
    UploadJob,
)
from data.services_write_helpers import add_and_flush, commit_and_refresh, commit_only, flush_only, rollback_only
from utils.variant_key import compute_variant_key

logger = logging.getLogger(__name__)


def get_upload_job(db: Session, job_id: int, user_id: int, is_admin: bool = False) -> dict:
    """Get a single upload job with full details."""
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job:
        raise Exception("Upload job not found")
    if job.supplier_id != user_id and not is_admin:
        raise Exception("Not your upload job")
    return job.to_dict()


def create_ai_upload_job(
    db: Session,
    supplier_id: int,
    images_data: list[dict],
    country_code: str,
    model_used: Optional[str] = None,
    prompt_hash: Optional[str] = None,
) -> dict:
    """Create a new AI upload job and save media files."""
    job = AIUploadJob(
        supplier_id=supplier_id,
        status="pending",
        model_used=model_used,
        prompt_hash=prompt_hash,
        source_media_json="[]",
        country_code=country_code,
    )
    add_and_flush(db, job)
    flush_only(db)

    media_list = []
    for img_info in images_data:
        key, url, content = img_info.get("key"), img_info.get("url"), img_info.get("content")
        media_list.append({"filename": img_info.get("filename"), "key": key, "url": url})

    job.source_media_json = json.dumps(media_list)

    if not media_list:
        raise Exception("No images could be saved.")

    commit_and_refresh(db, job)
    return {
        "job_id": job.id,
        "status": job.status,
        "country_code": job.country_code,
        "media_count": len(media_list),
    }


def get_ai_upload_job(
    db: Session,
    job_id: int,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """Get an AI upload job with staging products and logs."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise Exception("Job not found.")
    staging = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).offset(skip).limit(limit).all()
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


def _publish_staging(
    db: Session,
    staging: AIStagingProduct,
    overrides: Optional[dict],
    job: AIUploadJob,
    slugify_fn: callable,
) -> Product:
    """Publish a staging product to the products table."""
    name = (overrides or {}).get("name") or staging.name
    description = (overrides or {}).get("description") or staging.description
    category = (overrides or {}).get("category") or staging.category
    price = (overrides or {}).get("price") or staging.price or 0
    color = (overrides or {}).get("color") or staging.color
    brand = (overrides or {}).get("brand") or staging.brand

    slug = f"{slugify_fn(name) or 'product'}-{uuid.uuid4().hex[:8]}"
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
    add_and_flush(db, product)
    flush_only(db)

    variants = db.query(AIStagingVariant).filter(AIStagingVariant.staging_product_id == staging.id).all()
    total_stock = 0
    for sv in variants:
        v_overrides = (overrides or {}).get("variants", {}).get(str(sv.id)) if isinstance(overrides, dict) else None
        v_color = v_overrides.get("color", sv.color) if v_overrides else sv.color
        v_size = v_overrides.get("size", sv.size) if v_overrides else sv.size
        v_price = v_overrides.get("price", sv.price) if v_overrides else sv.price
        v_stock = int(v_overrides.get("stock", sv.stock) if v_overrides else sv.stock) or 0
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
        add_and_flush(db, variant)

    product.stock = total_stock
    return product


def publish_ai_upload_job(
    db: Session,
    job_id: int,
    overrides: Optional[dict] = None,
    slugify_fn: callable = None,
) -> dict:
    """Publish an AI upload job's staging products."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise Exception("Job not found.")
    if job.status not in ("staged", "failed"):
        raise Exception(f"Job is not ready to publish (status={job.status}).")

    staging_products = db.query(AIStagingProduct).filter(AIStagingProduct.job_id == job_id).all()
    if not staging_products:
        raise Exception("No staging products to publish.")

    created_ids = []
    for staging in staging_products:
        so = (overrides or {}).get(str(staging.id)) if isinstance(overrides, dict) else None
        product = _publish_staging(db, staging, so, job, slugify_fn or _default_slugify)
        created_ids.append(product.id)
        if job.created_product_id is None:
            job.created_product_id = product.id

    job.status = "completed"
    commit_only(db)
    return {"job_id": job.id, "status": "completed", "created_product_ids": created_ids}


def _default_slugify(name: str) -> str:
    """Default slugify function."""
    slug = (name or "").strip().lower()
    slug = "".join(ch if ch.isalnum() or ch in (" ", "-") else "-" for ch in slug)
    slug = slug.replace(" ", "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:60]


def cancel_ai_upload_job(db: Session, job_id: int) -> dict:
    """Cancel an AI upload job."""
    job = db.get(AIUploadJob, job_id)
    if job is None:
        raise Exception("Job not found.")
    if job.status in ("completed",):
        raise Exception("Job already completed.")
    job.status = "cancelled"
    commit_only(db)
    return {"job_id": job.id, "status": "cancelled"}


def process_ai_upload_job(job_id: int) -> None:
    """Worker: enrich a job's media and write staging rows. Runs in a worker thread."""
    from data.db import get_db_context

    with get_db_context() as db:
        job = db.get(AIUploadJob, job_id)
        if job is None:
            logger.warning("AI upload job %s not found", job_id)
            return
        if job.status not in ("pending", "failed"):
            logger.info("AI upload job %s already processed (status=%s)", job_id, job.status)
            return

        job.status = "processing"
        commit_only(db)

        media_list = []
        try:
            from services import ai_service

            parsed = json.loads(job.source_media_json or "[]")

            staging_products: list[AIStagingProduct] = []
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
                    add_and_flush(db, staging)
                    flush_only(db)
                    for v in variants:
                        v.staging_product_id = staging.id
                        v.variant_key = f"staged-{uuid.uuid4().hex}"
                        add_and_flush(db, v)
                    for log in logs:
                        add_and_flush(db, log)
                    staging_products.append(staging)
                    media_list.append({"path": image_url, "staging_id": staging.id})

                except Exception as exc:
                    logger.warning("AI enrichment failed for image %s in job %s: %s", image_url, job_id, exc)
                    add_and_flush(db, AIGenerationLog(
                        job_id=job.id, field="error", model_used="worker",
                        prompt_hash=None, tokens_used=None, cost=None, confidence=None,
                        country_code=job.country_code,
                    ))
                    continue

            job.source_media_json = json.dumps(media_list)
            if staging_products:
                job.status = "staged"
            else:
                job.status = "failed"
                job.error_log = "No images could be enriched."
            commit_only(db)
        except Exception as exc:
            rollback_only(db)
            job = db.get(AIUploadJob, job_id)
            if job:
                job.status = "failed"
                job.error_log = str(exc)[:2000]
                commit_only(db)
            logger.exception("AI upload job %s failed: %s", job_id, exc)


def batch_publish_products(
    db: Session,
    batch_results_json: str,
    current_user: dict,
    save_image_fn: callable,
    persist_product_fn: callable,
    max_batch_size: int = 20,
) -> dict:
    """Publish products from batch-analyze results.

    Takes the JSON response from batch-analyze and creates real Product records:
      - AI-detected name, category, description, tags
      - AI-suggested price + stock
      - AI-detected variants (colors, sizes) with per-variant stock
      - Saved BG-removed images
      - Auto-generated SEO slugs and product codes

    Returns the created product IDs and any errors per item.
    """
    try:
        batch_data = json.loads(batch_results_json)
    except (json.JSONDecodeError, TypeError) as exc:
        raise Exception(f"Invalid JSON: {exc}")

    results = batch_data.get("results", [])
    if not results:
        raise Exception("No results in batch data")

    if len(results) > max_batch_size:
        raise Exception(f"Maximum {max_batch_size} products per batch")

    published: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        for idx, item in enumerate(results):
            if item.get("status") != "completed":
                errors.append({
                    "index": idx,
                    "name": item.get("name_hint", f"Item {idx}"),
                    "error": item.get("error", "Analysis incomplete"),
                })
                continue

            try:
                analysis = item.get("analysis", {}) or {}
                price_data = item.get("price_suggestion", {}) or {}
                bg_b64 = item.get("bg_removed_b64", "")
                name_hint = item.get("name_hint", "")
                winner = item.get("winner_strategy", "general")

                product_name = (
                    analysis.get("product_name_hint")
                    or analysis.get("english_title")
                    or analysis.get("name")
                    or name_hint
                    or f"Product {idx + 1}"
                )
                product_name = str(product_name)[:200]

                category = analysis.get("suggested_category") or "General"
                subcategory = analysis.get("suggested_subcategory") or None
                description = (
                    analysis.get("english_description")
                    or analysis.get("product_description")
                    or f"{product_name} — Quality product from our catalog."
                )

                suggested_price = price_data.get("suggested_price") or analysis.get("ai_suggested_price") or 0
                try:
                    price = float(suggested_price) if suggested_price else 10.0
                except (TypeError, ValueError):
                    price = 10.0
                if price <= 0:
                    price = 10.0

                stock = 100
                stock_hints = analysis.get("stock_hints", {}) or {}
                if stock_hints:
                    total_stock = 0
                    for color_hints in stock_hints.values():
                        if isinstance(color_hints, dict):
                            total_stock += sum(
                                int(v) for v in color_hints.values() if isinstance(v, (int, float))
                            )
                    if total_stock > 0:
                        stock = total_stock

                tags_list = analysis.get("suggested_tags", []) or []
                tags = ", ".join(str(t) for t in tags_list if t)[:500] if tags_list else None

                attrs = analysis.get("detected_attributes", {}) or {}
                colors_list = attrs.get("color", []) or []
                color = ", ".join(str(c) for c in colors_list if c)[:200] if colors_list else None

                brand = analysis.get("suggested_brand") or attrs.get("brand") or None

                variants_payload = []
                variant_options = analysis.get("variant_options", {}) or {}

                if "color" in variant_options or "size" in variant_options:
                    colors = variant_options.get("color", ["Default"])
                    sizes = variant_options.get("size", ["One Size"])

                    for color_val in colors:
                        for size_val in sizes:
                            hints = stock_hints or {}
                            color_key = str(color_val) if color_val else "Default"
                            size_key = str(size_val) if size_val else "One Size"
                            item_stock = 0
                            if isinstance(hints, dict):
                                color_stock = hints.get(color_key, {}) or {}
                                if isinstance(color_stock, dict):
                                    item_stock = int(color_stock.get(size_key, 0) or 0)
                            if item_stock <= 0:
                                item_stock = 50

                            variants_payload.append({
                                "color": color_val,
                                "size": size_val,
                                "stock": item_stock,
                                "price": price,
                                "is_active": True,
                            })

                image_url = save_image_fn(bg_b64, current_user["id"], product_name)

                extra_attributes = {
                    "batch_upload": True,
                    "batch_index": idx,
                    "winner_strategy": winner,
                    "ai_source": analysis.get("source", "batch"),
                }

                new_product = persist_product_fn(
                    name=product_name,
                    description=description,
                    price=price,
                    stock_quantity=stock,
                    category=category,
                    subcategory=subcategory,
                    color=color,
                    brand=brand,
                    tags=tags,
                    sizes=None,
                    materials=None,
                    visibility_regions=[],
                    weight=None,
                    dimensions=None,
                    compare_price=None,
                    discount_starts_at=None,
                    discount_ends_at=None,
                    return_window_days=None,
                    is_active=True,
                    image_url=image_url,
                    video_url=None,
                    additional_media=[image_url] if image_url else None,
                    ai_description=description,
                    variants_payload=json.dumps(variants_payload) if variants_payload else None,
                    current_user=current_user,
                    db=db,
                    bg_preset=winner,
                    extra_attributes=extra_attributes,
                )

                flush_only(db)

                published.append({
                    "id": new_product.id,
                    "name": product_name,
                    "slug": new_product.slug or "",
                    "image_url": image_url,
                    "category": category,
                    "price": price,
                    "stock": stock,
                    "variants_count": len(variants_payload),
                })

            except Exception as exc:
                logger.exception("Failed to publish batch item %s: %s", idx, exc)
                errors.append({
                    "index": idx,
                    "name": item.get("name_hint", f"Item {idx}"),
                    "error": str(exc),
                })

        commit_only(db)
    except Exception as outer_exc:
        rollback_only(db)
        logger.exception("Batch publish outer error: %s", outer_exc)
        return {
            "total": len(results),
            "published": len(published),
            "failed": len(results) - len(published),
            "products": published,
            "errors": errors + [{"index": -1, "error": f"Batch aborted: {outer_exc}"}],
            "partial": True,
        }

    return {
        "total": len(results),
        "published": len(published),
        "failed": len(errors),
        "products": published,
        "errors": errors,
    }