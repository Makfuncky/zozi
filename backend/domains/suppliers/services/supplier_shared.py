"""Supplier service — shared constants and helper functions."""

"""
Supplier Controller — all supplier portal business logic:
orders, products, analytics, inventory, profile, payouts, bulk operations.
"""
import html
import csv
import io
import json
import os
import re
import subprocess
import sys
import uuid
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, List, Optional, cast
from urllib.parse import urlparse

from infrastructure.utils.datetime_utils import utcnow
from datetime import datetime

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import String, func, or_
from sqlalchemy.orm import Session, selectinload

from domains.governance.ports import User, BadgeBillingRecord, CommissionBadgeTier, SupplierBankAccount
from domains.catalog.ports import Product, ProductVariant
from domains.comms.ports import Notification, SupplierProfile
from domains.finance.ports import BankTransaction, SupplierSettlement, Payout
from domains.logistics.ports import LogisticsPartner, Shipment, ShipmentEvent
from domains.orders.ports import Order, OrderItem
# from providers.ai.ai_variant_config import ai_service  # unused
# TODO: Module not yet created
# from domains.finance.services.ledger.finance_transfer_service import build_transfer_reference
from domains.logistics.ports import normalize_country_code
from domains.audit.ports import AuditAction, audit_log
from infrastructure.utils.cache import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from domains.catalog.ports import _bump_product_cache_version
from infrastructure.utils.background_jobs import enqueue_job
from domains.orders.ports import canonical_scan_code, derive_order_financials, ensure_shipment_identifiers, order_status_label, reconcile_order_status, shipment_status_label
from infrastructure.utils.realtime import logistics_realtime_hub
from infrastructure.utils.config import settings
from kernel.money import to_decimal
from infrastructure.utils.variant_key import compute_variant_key

logger = logging.getLogger(__name__)


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }
_AI_IMAGE_SMOKE_REPORT = Path(__file__).resolve().parents[2] / "artifacts" / "ai_image_group_smoke.json"
_AI_IMAGE_SMOKE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ai_image_group_smoke.py"
_UNSET = object()
_PROFILE_JSON_ARRAY_FIELDS = {"certifications"}
_PROFILE_JSON_OBJECT_FIELDS = {"social_links"}
_PUBLIC_SUPPLIER_CACHE_TTL = 120


def _build_public_supplier_cache_key(prefix: str, payload: dict[str, Any]) -> str:
    return build_versioned_cache_key("public_suppliers", prefix, payload)


def _normalize_optional_product_text(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_product_visibility_regions(value: object) -> list[str]:
    if value in (None, "", [], (), {}):
        return []

    parsed = value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = [item.strip() for item in raw.split(",") if item.strip()]

    if not isinstance(parsed, list):
        raise HTTPException(status_code=400, detail="visibility_regions must be a list or JSON array string")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        candidate = str(item).strip()
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(candidate[:100])
    return normalized[:200]


def _serialize_product_visibility_regions(value: object) -> list[str]:
    if value in (None, "", [], (), {}):
        return []
    try:
        return _normalize_product_visibility_regions(value)
    except HTTPException:
        return []


def _load_shipments_for_orders(order_ids: list[int], db: Session) -> dict[int, list[Shipment]]:
    if not order_ids:
        return {}

    shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id.in_(order_ids))
        .order_by(Shipment.order_id.asc(), Shipment.created_at.asc(), Shipment.id.asc())
        .all()
    )

    shipments_by_order: dict[int, list[Shipment]] = {}
    for shipment in shipments:
        shipments_by_order.setdefault(cast(int, shipment.order_id), []).append(shipment)
    return shipments_by_order


def _load_users_by_ids(user_ids: list[int], db: Session) -> dict[int, User]:
    if not user_ids:
        return {}

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return {cast(int, user.id): user for user in users}


def _parse_optional_datetime(value: Optional[object]) -> Optional[datetime]:
    if value in (None, "", b""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)


def _persist_supplier_product(
    *,
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    subcategory: Optional[str],
    color: Optional[str],
    brand: Optional[str],
    tags: Optional[str],
    sizes: Optional[str],
    materials: Optional[str],
    visibility_regions: Optional[object],
    weight: Optional[float],
    dimensions: Optional[str],
    compare_price: Optional[float],
    discount_starts_at: Optional[datetime],
    discount_ends_at: Optional[datetime],
    return_window_days: Optional[int],
    is_active: bool,
    image_url: Optional[str],
    video_url: Optional[str],
    ai_description: Optional[str],
    variants_payload: Optional[object],
    current_user: dict,
    db: Session,
    variant_axes: Optional[object] = None,
    bg_preset: Optional[str] = None,
    extra_attributes: Optional[dict] = None,
) -> Product:
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
        return_window_days,
        supplier_id=current_user["id"],
        db=db,
    )
    parsed_variants = _parse_product_variants_payload(variants_payload)
    normalized_subcategory = _normalize_optional_product_text(subcategory)
    normalized_visibility_regions = _normalize_product_visibility_regions(visibility_regions)

    # Map the free-text category to a seeded taxonomy row (graceful if absent).
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
        from domains.catalog.ports import ProductVideo
        db.add(ProductVideo(product_id=new_product.id, video_url=video_url, upload_status="completed"))
    if parsed_variants:
        _replace_product_variants(new_product, parsed_variants, db)
    return new_product


def _map_bulk_upload_error(detail: object) -> dict[str, object]:
    message = str(detail or "").strip()
    lowered = message.lower()

    variant_match = re.search(r"variant\s+#(\d+)\s+(stock|price)", lowered)
    if variant_match:
        return {
            "variant_index": max(int(variant_match.group(1)) - 1, 0),
            "variant_field_key": variant_match.group(2),
        }

    if "name is required" in lowered:
        return {"field_key": "name"}
    if "price must be a number" in lowered or "price must be > 0" in lowered or "price cannot be negative" in lowered:
        return {"field_key": "price"}
    if "return window" in lowered:
        return {"field_key": "return-window"}
    if "visibility_regions" in lowered:
        return {"field_key": "visibility"}
    if "category" in lowered:
        return {"field_key": "category"}
    if "subcategory" in lowered:
        return {"field_key": "subcategory"}
    if "image" in lowered or "video" in lowered:
        return {"field_key": "image-mode"}
    return {}


def _build_bulk_upload_error(index: int, detail: object, *, name: Optional[str] = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "index": index,
        "error": str(detail),
    }
    if name:
        payload["name"] = name
    payload.update(_map_bulk_upload_error(detail))
    return payload


def _load_supplier_ai_audit_summary() -> Optional[dict[str, Any]]:
    try:
        if not _AI_IMAGE_SMOKE_REPORT.is_file():
            return None
        raw = json.loads(_AI_IMAGE_SMOKE_REPORT.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read supplier AI smoke artifact: %s", exc)
        return None

    if not isinstance(raw, dict):
        return None

    results = raw.get("results") if isinstance(raw.get("results"), list) else []
    curated_groups: list[dict[str, Any]] = []
    for entry in results:
        if not isinstance(entry, dict):
            continue
        expectations = entry.get("expectations") if isinstance(entry.get("expectations"), dict) else {}
        is_curated = any(bool(value) for value in expectations.values())
        if not is_curated:
            continue
        group_summary = {
            "id": entry.get("id"),
            "label": entry.get("label"),
            "status": entry.get("status") or ("FAIL" if entry.get("errors") else "WARN" if entry.get("warnings") else "OK"),
            "files": entry.get("files") or [],
            "expectations": expectations,
            "result": entry.get("result") or {},
            "warnings": entry.get("warnings") or [],
            "errors": entry.get("errors") or [],
        }
        curated_groups.append(group_summary)

    status_rank = {"FAIL": 0, "WARN": 1, "OK": 2}
    curated_groups.sort(key=lambda item: (status_rank.get(str(item.get("status")), 3), str(item.get("label") or "")))
    attention_groups = [group for group in curated_groups if group["status"] != "OK"]

    return {
        "generatedAt": raw.get("generated_at"),
        "groupCount": raw.get("group_count") or 0,
        "curatedGroupCount": len(curated_groups),
        "errorCount": raw.get("error_count") or 0,
        "warningCount": raw.get("warning_count") or 0,
        "attentionCount": len(attention_groups),
        "curatedGroups": curated_groups,
        "attentionGroups": attention_groups,
    }


def run_supplier_ai_audit(limit: int = 0) -> dict[str, Any]:
    if not _AI_IMAGE_SMOKE_SCRIPT.is_file():
        raise RuntimeError(f"AI smoke script not found: {_AI_IMAGE_SMOKE_SCRIPT}")

    command = [sys.executable, str(_AI_IMAGE_SMOKE_SCRIPT), "--output", str(_AI_IMAGE_SMOKE_REPORT)]
    if limit > 0:
        command.extend(["--limit", str(limit)])

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "AI smoke run failed").strip()
        raise RuntimeError(message)

    summary = _load_supplier_ai_audit_summary()
    if summary is None:
        raise RuntimeError("AI smoke run completed but no audit summary was produced")

    return {
        "filename": str(_AI_IMAGE_SMOKE_REPORT.name),
        "path": str(_AI_IMAGE_SMOKE_REPORT),
        "aiAudit": summary,
    }


def queue_supplier_ai_audit(current_user: dict, limit: int = 0) -> dict[str, Any]:
    return enqueue_job(
        kind="supplier-ai-audit",
        owner_user_id=current_user["id"],
        owner_role=current_user["role"],
        metadata={"limit": limit, "filename": _AI_IMAGE_SMOKE_REPORT.name},
        func=lambda: run_supplier_ai_audit(limit=limit),
    )


def _parse_optional_return_window_days(value: Optional[object]) -> Optional[int]:
    if value in (None, "", b""):
        return None
    try:
        candidate: int | str | bytes = value if isinstance(value, (int, str, bytes)) else str(value)
        days = int(candidate)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Return window must be an integer") from exc
    if days < 10:
        raise HTTPException(status_code=400, detail="Return window must be at least 10 days")
    return days


def _get_supplier_max_return_window_days(supplier_id: int, db: Session) -> int:
    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    raw_value = getattr(supplier_profile, "max_return_days", None) if supplier_profile else None
    try:
        candidate: int | str | bytes = raw_value if isinstance(raw_value, (int, str, bytes)) else str(raw_value)
        parsed = int(candidate)
    except (TypeError, ValueError):
        parsed = 30
    return max(10, parsed)


def _parse_supplier_return_window_days(
    value: Optional[object],
    *,
    supplier_id: int,
    db: Session,
) -> Optional[int]:
    days = _parse_optional_return_window_days(value)
    if days is None:
        return None
    max_days = _get_supplier_max_return_window_days(supplier_id, db)
    if days > max_days:
        raise HTTPException(
            status_code=400,
            detail=f"Return window cannot exceed your configured maximum of {max_days} days",
        )
    return days


def _coerce_optional_bool(value: Optional[object], default: bool = True) -> bool:
    if value in (None, "", b""):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return bool(value)


def _sanitize_profile_string(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value)
    normalized = value.strip()
    return html.escape(normalized) if normalized else None


def _sanitize_profile_json(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_profile_string(value)
    if isinstance(value, list):
        return [_sanitize_profile_json(item) for item in value if item not in (None, "")]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key).strip()
            if not key:
                continue
            sanitized_value = _sanitize_profile_json(raw_value)
            if sanitized_value in (None, "", [], {}):
                continue
            sanitized[key] = sanitized_value
        return sanitized
    return value


def _normalize_product_video_reference(value: Optional[object]) -> Optional[str]:
    if value in (None, "", b""):
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    lower = normalized.lower()
    if lower.startswith(("/uploads/", "uploads/")):
        if lower.endswith((".mp4", ".webm")):
            return normalized
        raise HTTPException(status_code=400, detail="Product video must be an MP4 or WebM file")
    if lower.startswith(("http://", "https://")):
        try:
            parsed = urlparse(normalized)
            hostname = (parsed.hostname or "").replace("www.", "").lower()
            if hostname in {"youtube.com", "m.youtube.com", "youtu.be", "vimeo.com"} or hostname.endswith(".vimeo.com"):
                return normalized
        except Exception:
            pass
        if re.search(r"\.(mp4|webm)(?:$|[?#])", lower):
            return normalized
    raise HTTPException(status_code=400, detail="Product video must be a YouTube, Vimeo, MP4, or WebM reference")


def _resolve_category_id(category: Optional[str], db: Session) -> Optional[int]:
    """Map a free-text category label to a seeded ``categories`` row id."""
    if not category:
        return None
    text = str(category).strip()
    if not text:
        return None
    from domains.catalog.ports import Category

    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    row = (
        db.query(Category.id)
        .filter((Category.slug == slug) | (Category.name == text))
        .first()
    )
    if row:
        return row[0]
    # Fall back to a case-insensitive name match (e.g. AI label "Apparel" -> "Clothing").
    like = f"%{text}%"
    row = db.query(Category.id).filter(Category.name.ilike(like)).first()
    return row[0] if row else None


def _normalize_variant_axes(value: object) -> Optional[list]:
    """Validate/normalize the product-level variant axis definitions."""
    if value in (None, "", b""):
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    if not isinstance(value, list):
        return None
    axes: list = []
    for axis in value:
        if not isinstance(axis, dict):
            continue
        key = str(axis.get("key") or "").strip()
        if not key:
            continue
        axes.append({
            "key": key,
            "label": str(axis.get("label") or key).strip(),
            "options": [str(o).strip() for o in (axis.get("options") or []) if str(o).strip()],
        })
    return axes or None


def _normalize_variant_attributes(value: object) -> dict[str, str]:
    if value in (None, "", b""):
        return {}
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    if not isinstance(parsed, dict):
        return {}
    normalized: dict[str, str] = {}
    for raw_key, raw_value in parsed.items():
        key = str(raw_key).strip()
        text = str(raw_value).strip()
        if key and text:
            normalized[html.escape(key)] = html.escape(text)
    return normalized


def _build_variant_title(size: Optional[str], color: Optional[str], material: Optional[str], attributes: dict[str, str], fallback: Optional[str]) -> str:
    if fallback:
        return fallback
    parts = [size or "", color or "", material or "", *attributes.values()]
    title = " / ".join(part for part in parts if part)
    return title or "Variant"


def _product_code_segment(value: Optional[object], fallback: str, max_length: int) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())[:max_length]
    return normalized or fallback


def _generate_variant_product_code(product: Product, variant_payload: dict[str, object], index: int) -> str:
    category_code = _product_code_segment(getattr(product, "category", None), "GEN", 3)
    name_code = _product_code_segment(getattr(product, "name", None), "ITEM", 5)
    option_code = _product_code_segment(
        variant_payload.get("size") or variant_payload.get("color") or variant_payload.get("title"),
        f"V{index + 1:02d}",
        4,
    )
    return f"PRD-{category_code}-{name_code}-{option_code}-{int(product.id):06d}-{index + 1:02d}"


def _parse_product_variants_payload(value: Optional[object]) -> list[dict[str, object]]:
    if value in (None, "", b""):
        return []
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid variants JSON payload") from exc
    if not isinstance(parsed, list):
        raise HTTPException(status_code=400, detail="Variants must be a JSON array")
    if len(parsed) > 1000:
        raise HTTPException(status_code=400, detail="A product can include up to 1000 variants")

    variants: list[dict[str, object]] = []
    seen_codes: dict[str, set[str]] = {"sku": set(), "barcode": set(), "product_code": set()}

    for index, raw_variant in enumerate(parsed):
        if not isinstance(raw_variant, dict):
            raise HTTPException(status_code=400, detail=f"Variant #{index + 1} must be an object")

        size = _sanitize_profile_string(raw_variant.get("size"))
        color = _sanitize_profile_string(raw_variant.get("color"))
        material = _sanitize_profile_string(raw_variant.get("material"))
        pattern = _sanitize_profile_string(raw_variant.get("pattern"))
        gender = _sanitize_profile_string(raw_variant.get("gender"))
        title = _sanitize_profile_string(raw_variant.get("title"))
        sku = _sanitize_profile_string(raw_variant.get("sku"))
        barcode = _sanitize_profile_string(raw_variant.get("barcode"))
        product_code = _sanitize_profile_string(raw_variant.get("product_code"))
        image_url = _sanitize_profile_string(raw_variant.get("image_url"))
        attributes = _normalize_variant_attributes(raw_variant.get("attributes") or raw_variant.get("attributes_json"))
        is_active = _coerce_optional_bool(raw_variant.get("is_active"), True)

        try:
            stock = int(raw_variant.get("stock", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Variant #{index + 1} stock must be an integer") from exc
        if stock < 0:
            raise HTTPException(status_code=400, detail=f"Variant #{index + 1} stock cannot be negative")

        raw_price = raw_variant.get("price")
        try:
            price = float(raw_price) if raw_price not in (None, "") else None
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Variant #{index + 1} price must be a number") from exc
        if price is not None and price < 0:
            raise HTTPException(status_code=400, detail=f"Variant #{index + 1} price cannot be negative")

        sort_order_raw = raw_variant.get("sort_order", index)
        try:
            sort_order = int(sort_order_raw)
        except (TypeError, ValueError):
            sort_order = index

        title = _build_variant_title(size, color, material, attributes, title)

        for field_name, field_value in (("sku", sku), ("barcode", barcode), ("product_code", product_code)):
            if field_value:
                normalized_code = field_value.lower()
                if normalized_code in seen_codes[field_name]:
                    raise HTTPException(status_code=400, detail=f"Duplicate variant {field_name} '{field_value}'")
                seen_codes[field_name].add(normalized_code)

        variants.append({
            "title": title,
            "size": size,
            "color": color,
            "material": material,
            "pattern": pattern,
            "gender": gender,
            "sku": sku,
            "barcode": barcode,
            "product_code": product_code,
            "price": price,
            "stock": stock,
            "image_url": image_url,
            "attributes_json": json.dumps(attributes) if attributes else None,
            "is_active": is_active,
            "sort_order": sort_order,
        })

    return variants


def _replace_product_variants(product: Product, variants_payload: list[dict[str, object]], db: Session) -> None:
    """Idempotent upsert of product variants by ``variant_key`` (Phase 3b).

    Replaces the old delete+reinsert behaviour. Matching variants are updated
    in place (price/stock/media) and reactivated; new variants are inserted;
    variants present in the DB but absent from the payload are **soft-*
    deactivated** (``is_active=False``) so historical ``order_items.variant_id``
    references stay resolvable. Duplicate physical variants within a payload are
    collapsed into one with summed stock (recommended collision policy).
    """
    variants = list(getattr(product, "variants", []) or [])
    existing_by_key: dict[str, ProductVariant] = {
        v.variant_key: v for v in variants if getattr(v, "variant_key", None)
    }
    seen_keys: set[str] = set()
    processed: dict[str, ProductVariant] = {}

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
            # Collapse duplicate physical variant: sum stock, keep higher price.
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

    # Soft-deactivate variants that are no longer part of this product's payload.
    for variant in variants:
        vkey = getattr(variant, "variant_key", None)
        if vkey and vkey not in seen_keys:
            variant.is_active = False

    db.flush()


def _serialize_product_variant(variant: ProductVariant, product_price: object) -> dict[str, object]:
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
        "attributes": {str(key): str(value) for key, value in attributes.items()},
        "is_active": variant.is_active,
        "sort_order": variant.sort_order,
        "country_code": variant.country_code,
        "created_at": variant.created_at.isoformat() if variant.created_at else None,
        "updated_at": variant.updated_at.isoformat() if variant.updated_at else None,
    }


def _slugify_supplier_storefront(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"^-+|-+$", "", re.sub(r"[\s_-]+", "-", re.sub(r"[^\w\s-]", "", value.lower().strip())))


def _deserialize_profile_json(raw: Any, default: Any) -> Any:
    if raw in (None, "", b""):
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        parsed = json.loads(raw)
    except Exception:
        return default
    return parsed if isinstance(parsed, type(default)) else default


def _serialize_profile_json(value: Any, expected: str) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return "[]" if expected == "array" else "{}"
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid {expected} JSON payload") from exc

    if expected == "array":
        if value in (None, ""):
            value = []
        if not isinstance(value, list):
            raise HTTPException(status_code=400, detail="Certifications must be a JSON array")
    else:
        if value in (None, ""):
            value = {}
        if not isinstance(value, dict):
            raise HTTPException(status_code=400, detail="Social links must be a JSON object")

    return json.dumps(_sanitize_profile_json(value))


def _build_supplier_product_payload(product: Product, sales_count: int = 0, revenue: float = 0.0) -> dict:
    price = product.price
    compare_price = product.compare_price
    if compare_price and compare_price > (price or 0) and price:
        discount_pct: Optional[float] = round((float(compare_price) - float(price)) / float(compare_price) * 100, 2)
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
        "variants": [_serialize_product_variant(variant, product.price) for variant in (product.variants or [])],
        "created_at": product.created_at.isoformat(),
        "sales_count": sales_count,
        "revenue": revenue,
    }


# ── Orders ────────────────────────────────────────────────────────────────────

