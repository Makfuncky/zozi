"""Supplier Product Command Service — product persistence and variant management.

Deep module: owns the full lifecycle of supplier product creation and variant management.
Extracted from supplier_shared.py to improve locality and testability.

Locality: product creation bugs concentrate here, not in a shared utility file.
Leverage: one interface for product persistence, called by routers and bulk upload.
"""
from __future__ import annotations

import html
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.suppliers.services.supplier_shared import (
    _normalize_variant_axes,
    _normalize_optional_product_text,
    _normalize_product_visibility_regions,
    _parse_product_variants_payload,
    _parse_supplier_return_window_days,
    _resolve_category_id,
    _serialize_product_visibility_regions,
)
from infrastructure.storage.storage import storage as _storage

logger = logging.getLogger(__name__)


def _save_upload(content: bytes, user_id: int, filename: str | None = None, content_type: str | None = None) -> str:
    """Save an upload to object storage and return its URL."""
    ext = filename.rsplit(".", 1)[-1] if filename and "." in filename else "jpg"
    key = f"suppliers/{user_id}/uploads/{uuid.uuid4().hex[:8]}.{ext}"
    return _storage.save(key, content, content_type=content_type)


def persist_supplier_product(
    *,
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    subcategory: str | None = None,
    color: str | None = None,
    brand: str | None = None,
    tags: str | None = None,
    sizes: str | None = None,
    materials: str | None = None,
    visibility_regions: object = None,
    weight: float | None = None,
    dimensions: str | None = None,
    compare_price: float | None = None,
    discount_starts_at: datetime | None = None,
    discount_ends_at: datetime | None = None,
    return_window_days: int | None = None,
    is_active: bool = True,
    image_url: str | None = None,
    video_url: str | None = None,
    ai_description: str | None = None,
    variants_payload: object = None,
    current_user: Any = None,
    db: Session = None,
    variant_axes: object = None,
    bg_preset: str | None = None,
    extra_attributes: dict | None = None,
):
    """Persist a new supplier product with variants and media.

    This is the canonical entry point for product creation. It handles:
    - Category resolution and country restriction checks
    - Slug generation with collision avoidance
    - Variant parsing and deduplication
    - Video association
    - Visibility region normalization
    """
    from domains.catalog.ports import Product, ProductVideo

    supplier_country = str(current_user.get("preferred_country") or "").strip()
    country_code = current_user.get("country_code") or supplier_country or None
    if supplier_country:
        from domains.country.ports import is_product_restricted_for_country
        if is_product_restricted_for_country(category, supplier_country, db):
            raise HTTPException(
                status_code=422,
                detail=f"Products in category '{category}' are restricted in your country ({supplier_country}).",
            )

    normalized_return_window_days = _parse_supplier_return_window_days(
        return_window_days, supplier_id=current_user["id"], db=db,
    )
    parsed_variants = _parse_product_variants_payload(variants_payload)
    normalized_subcategory = _normalize_optional_product_text(subcategory)
    normalized_visibility_regions = _normalize_product_visibility_regions(visibility_regions)
    category_id = _resolve_category_id(category, db)

    # Generate unique product slug from name
    slug_base = re.sub(r"[^a-z0-9]+", "-", (name or "product").strip().lower()).strip("-") or "product"
    product_slug = slug_base
    attempt = 0
    while db.query(Product).filter(Product.slug == product_slug).first():
        attempt += 1
        product_slug = f"{slug_base}-{attempt}"

    new_product = Product(
        name=html.escape(name.strip()) if name else name,
        slug=product_slug,
        description=html.escape(description) if description else description,
        price=price,
        image_url=image_url,
        stock=stock_quantity,
        category=category,
        subcategory=normalized_subcategory,
        color=color,
        brand=brand,
        tags=tags,
        sizes=sizes,
        materials=materials,
        visibility_regions=json.dumps(normalized_visibility_regions) if normalized_visibility_regions else None,
        weight=weight,
        dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=normalized_return_window_days,
        ai_description=ai_description,
        is_active=is_active,
        supplier_id=current_user["id"],
        country_code=country_code,
        category_id=category_id,
        variant_axes=_normalize_variant_axes(variant_axes),
        bg_preset=bg_preset,
        attributes=json.dumps(extra_attributes) if extra_attributes else None,
    )
    db.add(new_product)
    db.flush()

    if video_url:
        db.add(ProductVideo(product_id=new_product.id, video_url=video_url, upload_status="completed"))

    if parsed_variants:
        replace_product_variants(new_product, parsed_variants, db)

    return new_product


def replace_product_variants(product: object, variants_payload: list[dict[str, object]], db: Session) -> None:
    """Idempotent upsert of product variants by variant_key.

    Replaces the old delete+reinsert behaviour. Matching variants are updated
    in place (price/stock/media) and reactivated; new variants are inserted;
    variants present in the DB but absent from the payload are soft-deactivated
    so historical order_items.variant_id references stay resolvable.
    """
    from domains.catalog.ports import ProductVariant
    from infrastructure.utils.variant_key import compute_variant_key

    variants = list(getattr(product, "variants", []) or [])
    existing_by_key = {v.variant_key: v for v in variants if getattr(v, "variant_key", None)}
    seen_keys: set[str] = set()
    processed: dict[str, object] = {}

    _UPSERT_FIELDS = (
        "title", "size", "color", "material", "pattern", "gender",
        "sku", "barcode", "product_code", "price", "stock",
        "media_url", "attributes_json", "is_active", "sort_order",
    )

    for index, variant_payload in enumerate(variants_payload):
        payload = dict(variant_payload)
        key = compute_variant_key(
            product.id,
            payload.get("size"), payload.get("color"), payload.get("material"),
            payload.get("pattern"), payload.get("gender"),
        )
        payload["variant_key"] = key

        if key in processed:
            prev = processed[key]
            prev.stock = (prev.stock or 0) + (payload.get("stock") or 0)
            if payload.get("price") is not None and (prev.price is None or payload["price"] > prev.price):
                prev.price = payload["price"]
            continue

        if not payload.get("product_code"):
            payload["product_code"] = _generate_variant_product_code(product, payload, index)
        payload.pop("name", None)
        payload["country_code"] = product.country_code

        seen_keys.add(key)
        existing = existing_by_key.get(key)
        if existing is not None:
            for field in _UPSERT_FIELDS:
                if field in payload:
                    setattr(existing, field, payload[field])
            existing.is_active = True
            processed[key] = existing
        else:
            new_variant = ProductVariant(product_id=product.id, **payload)
            db.add(new_variant)
            processed[key] = new_variant

    for variant in variants:
        vkey = getattr(variant, "variant_key", None)
        if vkey and vkey not in seen_keys:
            variant.is_active = False

    db.flush()


def _generate_variant_product_code(product: object, variant_payload: dict[str, object], index: int) -> str:
    """Generate a unique product code for a variant."""
    def _segment(value: object, fallback: str, max_length: int) -> str:
        return re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())[:max_length] or fallback

    category_code = _segment(getattr(product, "category", None), "GEN", 3)
    name_code = _segment(getattr(product, "name", None), "ITEM", 5)
    option_code = _segment(
        variant_payload.get("size") or variant_payload.get("color") or variant_payload.get("title"),
        f"V{index + 1:02d}", 4,
    )
    return f"PRD-{category_code}-{name_code}-{option_code}-{int(product.id):06d}-{index + 1:02d}"


def serialize_product_variant(variant: object, product_price: object) -> dict[str, object]:
    """Serialize a product variant for API responses."""
    try:
        attributes = json.loads(variant.attributes_json) if variant.attributes_json else {}
        if not isinstance(attributes, dict):
            attributes = {}
    except (TypeError, ValueError, json.JSONDecodeError):
        attributes = {}

    effective_price = float(variant.price) if variant.price is not None else float(product_price or 0)
    return {
        "id": variant.id,
        "product_id": variant.product_id,
        "name": variant.title or "Variant",
        "title": variant.title,
        "size": variant.size,
        "color": variant.color,
        "material": variant.material,
        "pattern": variant.pattern,
        "gender": variant.gender,
        "sku": variant.sku,
        "barcode": variant.barcode,
        "product_code": variant.product_code,
        "price": float(variant.price) if variant.price is not None else None,
        "effective_price": effective_price,
        "stock": variant.stock,
        "media_url": variant.media_url,
        "attributes": {str(k): str(v) for k, v in attributes.items()},
        "is_active": variant.is_active,
        "sort_order": variant.sort_order,
        "country_code": variant.country_code,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "updated_at": variant.updated_at.isoformat() if variant.updated_at else None,
    }


def build_supplier_product_payload(product: object, sales_count: int = 0, revenue: float = 0.0) -> dict:
    """Build a complete product payload for API responses."""
    price = product.price
    compare_price = product.compare_price
    if compare_price and compare_price > (price or 0) and price:
        discount_pct = round((float(compare_price) - float(price)) / float(compare_price) * 100, 2)
    else:
        discount_pct = None

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": product.price,
        "compare_price": product.compare_price,
        "discount_percentage": discount_pct,
        "discount_starts_at": product.discount_starts_at.isoformat() if product.discount_starts_at else None,
        "discount_ends_at": product.discount_ends_at.isoformat() if product.discount_ends_at else None,
        "image_url": product.image_url,
        "video_url": product.videos[0].video_url if product.videos else None,
        "stock": product.stock,
        "low_stock_threshold": product.low_stock_threshold,
        "is_featured": product.is_featured,
        "category": product.category,
        "subcategory": product.subcategory,
        "brand": product.brand,
        "rating": product.rating,
        "color": product.color,
        "tags": product.tags,
        "ai_description": product.ai_description,
        "sizes": product.sizes,
        "materials": product.materials,
        "visibility_regions": _serialize_product_visibility_regions(product.visibility_regions),
        "additional_images": product.images,
        "weight": product.weight,
        "dimensions": product.dimensions,
        "return_window_days": product.return_window_days,
        "supplier_id": product.supplier_id,
        "is_active": product.is_active,
        "is_new": product.is_new,
        "is_digital": product.is_digital,
        "is_verified": product.is_verified,
        "moderation_status": product.moderation_status,
        "category_id": product.category_id,
        "variant_axes": product.variant_axes,
        "bg_preset": product.bg_preset,
        "view_count": getattr(product, "view_count", 0),
        "rating_count": getattr(product, "rating_count", 0),
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "variants": [serialize_product_variant(v, product.price) for v in (product.variants or [])],
        "created_at": product.created_at.isoformat(),
        "sales_count": sales_count,
        "revenue": revenue,
    }
