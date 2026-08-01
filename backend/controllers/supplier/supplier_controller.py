"""
Supplier Controller â€” all supplier portal business logic:
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

from utils.datetime_utils import utcnow
from datetime import datetime

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import String, func, or_
from sqlalchemy.orm import Session, selectinload

from models import BadgeBillingRecord, BankTransaction, CommissionBadgeTier, LogisticsPartner, Order, OrderItem, Payout, Product, ProductVariant, Shipment, ShipmentEvent, SupplierProfile, SupplierBankAccount, SupplierSettlement, User
from services import ai_service
from services.suppliers_write_service import (
    add_and_flush,
    add_to_session,
    commit_and_refresh,
    commit_session,
    create_supplier_bank_account,
    create_supplier_payout_request,
    create_supplier_profile,
    flush_session,
    stage_notification,
    update_supplier_bank_account,
)
from services.logistics_partner_pricing import normalize_country_code
from utils.audit_log import audit_log, AuditAction
from utils.cache import build_versioned_cache_key, bump_cache_version, cache_get_json, cache_set_json
from services.catalog.product_utils import _bump_product_cache_version
from utils.background_jobs import enqueue_job
from utils.order_tracking import canonical_scan_code, derive_order_financials, ensure_shipment_identifiers, order_status_label, reconcile_order_status, shipment_status_label
from utils.realtime import logistics_realtime_hub
from utils.config import settings
from utils.money import to_decimal
from utils.variant_key import compute_variant_key

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
_SUPPLIER_PROFILE_MEDIA_FIELDS = {
    "logo_url": {"kind": "image", "label": "logo", "max_size": 10 * 1024 * 1024},
    "banner_url": {"kind": "image", "label": "banner", "max_size": 10 * 1024 * 1024},
    "video_url": {"kind": "video", "label": "video", "max_size": 25 * 1024 * 1024},
    "certification_image": {"kind": "image", "label": "certification", "max_size": 10 * 1024 * 1024},
}
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
    additional_media: Optional[list[str]],
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
        from controllers.country_controller import is_product_restricted_for_country
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
        images=json.dumps(additional_media) if additional_media else None,
        ai_description=ai_description,
        is_active=is_active,
        supplier_id=current_user["id"],
        country_code=country_code,
        category_id=category_id,
        variant_axes=_normalize_variant_axes(variant_axes),
        bg_preset=bg_preset,
        attributes=json.dumps(extra_attributes) if extra_attributes else None,
    )
    add_and_flush(db, new_product)
    if video_url:
        from models import ProductVideo
        add_to_session(db, ProductVideo(product_id=new_product.id, video_url=video_url, upload_status="completed"))
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
    if "gallery media items" in lowered or "image" in lowered or "video" in lowered:
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


def _normalize_media_path(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return None
    if normalized.startswith(("http://", "https://", "blob:", "data:")):
        return normalized
    if normalized.startswith("/uploads/"):
        return normalized
    if normalized.startswith("uploads/"):
        return f"/{normalized}"
    if "/" not in normalized and "." in normalized:
        return f"/uploads/{normalized}"
    return normalized


def _normalize_product_video_reference(value: Optional[object]) -> Optional[str]:
    if value in (None, "", b""):
        return None
    normalized = _normalize_media_path(str(value))
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
    from models import Category

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
        media_url = _normalize_media_path(_sanitize_profile_string(raw_variant.get("media_url") or raw_variant.get("image_url")))
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
            "media_url": media_url,
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
            add_to_session(db, new_variant)
            processed[key] = new_variant

    # Soft-deactivate variants that are no longer part of this product's payload.
    for variant in variants:
        vkey = getattr(variant, "variant_key", None)
        if vkey and vkey not in seen_keys:
            variant.is_active = False

    flush_session(db)


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


# â”€â”€ Orders â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_orders(
    current_user: dict,
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    supplier_id = current_user["id"]
    order_id_query = (
        db.query(Order.id.label("order_id"), Order.created_at.label("created_at"))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .distinct()
    )
    if status and status != "all":
        order_id_query = order_id_query.filter(Order.status == status)
    if search and search.strip():
        term = f"%{search.strip()}%"
        order_id_query = order_id_query.outerjoin(User, User.id == Order.user_id).filter(
            or_(
                func.cast(Order.id, String).ilike(term),
                User.username.ilike(term),
                User.email.ilike(term),
            )
        )
    total = order_id_query.count()
    query = order_id_query.order_by(Order.created_at.desc(), Order.id.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    paged_order_ids = [cast(int, row.order_id) for row in query.all()]
    if not paged_order_ids:
        resolved_page_size = limit if limit is not None else 0
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_page_size)

    supplier_orders = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id.in_(paged_order_ids))
        .all()
    )
    order_positions = {order_id: index for index, order_id in enumerate(paged_order_ids)}
    supplier_orders.sort(key=lambda order: order_positions.get(cast(int, order.id), len(order_positions)))
    shipments_by_order = _load_shipments_for_orders([cast(int, order.id) for order in supplier_orders], db)
    shipment_ids = [cast(int, shipment.id) for shipments in shipments_by_order.values() for shipment in shipments]
    shipment_events_by_shipment: dict[int, list[ShipmentEvent]] = {}
    if shipment_ids:
        shipment_events = (
            db.query(ShipmentEvent)
            .filter(ShipmentEvent.shipment_id.in_(shipment_ids))
            .order_by(ShipmentEvent.created_at.asc(), ShipmentEvent.id.asc())
            .all()
        )
        for event in shipment_events:
            shipment_events_by_shipment.setdefault(cast(int, event.shipment_id), []).append(event)
    customers_by_id = _load_users_by_ids([cast(int, order.user_id) for order in supplier_orders], db)

    # Batch-load supplier settlements for payment/settlement status enrichment
    all_order_ids = [cast(int, order.id) for order in supplier_orders]
    settlements_by_order: dict[int, SupplierSettlement] = {}
    if all_order_ids:
        settlements_by_order = {
            cast(int, s.order_id): s
            for s in db.query(SupplierSettlement).filter(
                SupplierSettlement.supplier_id == supplier_id,
                SupplierSettlement.order_id.in_(all_order_ids),
            ).all()
        }

    result = []
    orders_updated = False
    for order in supplier_orders:
        shipments = shipments_by_order.get(cast(int, order.id), [])
        reconciled_status = reconcile_order_status(order, shipments)
        if order.status != reconciled_status:
            order.status = reconciled_status
            orders_updated = True

        supplier_shipments = [
            shipment
            for shipment in shipments
            if cast(Optional[int], getattr(shipment, "supplier_id", None)) == supplier_id
        ]
        preferred_shipment = supplier_shipments[-1] if supplier_shipments else None
        shipment_status = cast(Optional[str], getattr(preferred_shipment, "status", None)) if preferred_shipment else None
        shipment_events = []
        for shipment in shipments:
            shipment_events.extend(shipment_events_by_shipment.get(cast(int, shipment.id), []))

        status_label_value = order_status_label(reconciled_status, shipments, shipment_events)
        shipment_status_label_value = (
            shipment_status_label(shipment_status, shipment=preferred_shipment)
            if preferred_shipment and shipment_status
            else None
        )
        tracking_number = (
            cast(Optional[str], getattr(preferred_shipment, "tracking_number", None))
            or canonical_scan_code(preferred_shipment)
            if preferred_shipment
            else None
        )

        customer = customers_by_id.get(cast(int, order.user_id))
        order_financials = derive_order_financials(order)
        settlement = settlements_by_order.get(cast(int, order.id))
        supplier_items = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "product_name": item.product.name,
                "product_image": _normalize_media_path(item.product.image_url),
            }
            for item in order.items
            if item.product.supplier_id == supplier_id
        ]
        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "total_amount": order_financials["total"],
            "status": order.status,
            "status_label": status_label_value,
            "tracking_number": tracking_number,
            "shipment_status": shipment_status,
            "shipment_status_label": shipment_status_label_value,
            "payment_status": "paid" if getattr(order, "paid_at", None) else "unpaid",
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "payment_method": getattr(order, "payment_method", None),
            "settlement_status": cast(str, getattr(settlement, "status", None)) if settlement else None,
            "settlement_id": cast(int, getattr(settlement, "id", None)) if settlement else None,
            "settlement_net_amount": float(cast(object, getattr(settlement, "net_amount", None)) or 0) if settlement else None,
            "created_at": order.created_at.isoformat(),
            "customer_name": customer.username if customer else "Unknown",
            "customer_email": customer.email if customer else "",
            "customer_phone": order.customer_phone,
            "shipping_address": order.shipping_address,
            "delivery_location": order.delivery_location,
            "delivery_note": order.delivery_note,
            "items": supplier_items,
        })
    if orders_updated:
        commit_session(db)
    resolved_page_size = limit if limit is not None else len(result)
    return _build_list_page_payload(result, total, offset=offset, page_size=resolved_page_size)


def update_supplier_order_status(order_id: int, status_update: dict, current_user: dict, db: Session) -> dict:
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == current_user["id"],
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shipments = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == current_user["id"])
        .order_by(Shipment.created_at.desc())
        .all()
    )
    current_reconciled = reconcile_order_status(order, shipments)
    new_status = (status_update or {}).get("status", "").strip().lower()

    ALLOWED_SUPPLIER_TRANSITIONS = {
        "confirmed": ["processing"],
        "processing": ["prepared"],
        "prepared": ["processing"],
    }

    if new_status in ALLOWED_SUPPLIER_TRANSITIONS.get(current_reconciled, []):
        order.status = new_status
        commit_and_refresh(db, order)
        return {
            "message": f"Order status updated to '{new_status}'",
            "order_id": order.id,
            "status": order.status,
        }

    raise HTTPException(
        status_code=409,
        detail=(
            f"Cannot transition order status from '{current_reconciled}' to '{new_status}'. "
            "Supplier can only transition: confirmed -> processing -> shipped. "
            "Other status transitions (picking_up, in_transit, delivered) are derived "
            "automatically from logistics partner scan events."
        ),
    )


def get_supplier_order_detail(order_id: int, current_user: dict, db: Session) -> dict:
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == current_user["id"],
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shipments = _load_shipments_for_orders([cast(int, order.id)], db).get(cast(int, order.id), [])
    reconciled_status = reconcile_order_status(order, shipments)
    if order.status != reconciled_status:
        order.status = reconciled_status
        commit_and_refresh(db, order)

    customer = _load_users_by_ids([cast(int, order.user_id)], db).get(cast(int, order.user_id))
    order_financials = derive_order_financials(order)
    supplier_items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price,
            "product_name": item.product.name,
            "product_image": _normalize_media_path(item.product.image_url),
        }
        for item in order.items
        if item.product.supplier_id == current_user["id"]
    ]

    return {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order_financials["total"],
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "customer_name": customer.username if customer else "Unknown",
        "customer_email": customer.email if customer else "",
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "delivery_location": order.delivery_location,
        "delivery_note": order.delivery_note,
        "items": supplier_items,
    }


def get_supplier_label_payload(order_id: int, current_user: dict, db: Session) -> dict:
    supplier_id = current_user["id"]
    order_has_supplier_products = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == supplier_id,
        )
        .first()
    )
    if not order_has_supplier_products:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    supplier_user = db.query(User).filter(User.id == supplier_id).first()
    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()

    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .first()
    )

    customer = db.query(User).filter(User.id == order.user_id).first()
    supplier_items = []
    supplier_subtotal = 0.0
    for item in order.items:
        if not item.product or item.product.supplier_id != supplier_id:
            continue
        unit_price = float(item.price or 0)
        quantity = int(item.quantity or 0)
        line_total = unit_price * quantity
        supplier_subtotal += line_total
        supplier_items.append(
            {
                "order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    has_shipment = shipment is not None
    shipment_id = shipment.id if shipment else None
    shipment_status = shipment.status if shipment else "awaiting_shipment"
    shipment_status_label_value = shipment_status_label(shipment_status, shipment=shipment) if shipment else "Awaiting Shipment"
    scan_code = (
        shipment.scan_code or f"SHIP-{shipment.id}"
        if shipment
        else f"ORDER-{order.id}"
    )
    tracking_number = shipment.tracking_number if shipment else None
    shipment_carrier = getattr(shipment, "carrier", None) if shipment else None
    carrier_name = cast(Any, getattr(shipment, "carrier_name", None)) if shipment else None
    if not carrier_name and shipment_carrier is not None:
        carrier_name = getattr(shipment_carrier, "name", None)
    packaged_at = cast(Any, getattr(shipment, "packaged_at", None)) if shipment else None
    order_created_at = cast(Any, getattr(order, "created_at", None))
    order_paid_at = cast(Any, getattr(order, "paid_at", None))
    order_financials = derive_order_financials(order)
    vat_amount = order_financials["vat"]
    shipping_amount = order_financials["shipping"]
    discount_amount = order_financials["discount"]
    total_amount = order_financials["total"]
    order_subtotal = order_financials["subtotal"]
    allocation_ratio = supplier_subtotal / order_subtotal if order_subtotal > 0 and supplier_subtotal > 0 else (1.0 if supplier_subtotal > 0 else 0.0)
    supplier_discount = round(discount_amount * allocation_ratio, 2)
    supplier_vat = round(vat_amount * allocation_ratio, 2)
    supplier_shipping = round(shipping_amount * allocation_ratio, 2)
    supplier_total = round(supplier_subtotal - supplier_discount + supplier_vat + supplier_shipping, 2)
    if supplier_total <= 0 and supplier_subtotal > 0:
        supplier_total = round(total_amount if allocation_ratio >= 0.999 else supplier_subtotal, 2)

    supplier_name = None
    if supplier_profile and supplier_profile.business_name:
        supplier_name = supplier_profile.business_name
    elif supplier_user and supplier_user.username:
        supplier_name = supplier_user.username
    else:
        supplier_name = f"Supplier #{supplier_id}"

    supplier_address_parts = [
        cast(Optional[str], getattr(supplier_profile, "address", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "city", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "region", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "country", None)) if supplier_profile else None,
        cast(Optional[str], getattr(supplier_profile, "postal_code", None)) if supplier_profile else None,
    ]
    supplier_address = ", ".join(str(part).strip() for part in supplier_address_parts if part and str(part).strip()) or None

    return {
        "order_id": order.id,
        "shipment_id": shipment_id,
        "has_shipment": has_shipment,
        "sheet_mode": "shipment" if has_shipment else "packing",
        "invoice_number": f"INV-{order.id:06d}",
        "order_status": order.status,
        "shipment_status": shipment_status,
        "shipment_status_label": shipment_status_label_value,
        "ordered_at": order_created_at.isoformat() if order_created_at else None,
        "paid_at": order_paid_at.isoformat() if order_paid_at else None,
        "payment_method": cast(Optional[str], getattr(order, "payment_method", None)),
        "supplier_name": supplier_name,
        "supplier_email": cast(Optional[str], getattr(supplier_user, "email", None)) if supplier_user else None,
        "supplier_phone": cast(Optional[str], getattr(supplier_profile, "phone_business", None)) if supplier_profile else None,
        "supplier_address": supplier_address,
        "supplier_website": cast(Optional[str], getattr(supplier_profile, "website", None)) if supplier_profile else None,
        "supplier_tax_id": cast(Optional[str], getattr(supplier_profile, "tax_id", None)) if supplier_profile else None,
        "supplier_logo_url": cast(Optional[str], getattr(supplier_profile, "logo_url", None)) if supplier_profile else None,
        "customer_name": customer.username if customer else f"Customer #{order.user_id}",
        "customer_email": customer.email if customer else None,
        "customer_phone": order.customer_phone,
        "shipping_address": order.shipping_address,
        "delivery_location": order.delivery_location,
        "delivery_note": order.delivery_note,
        "carrier_name": carrier_name,
        "tracking_number": tracking_number or (scan_code if shipment else None),
        "scan_code": scan_code,
        "current_hub": shipment.current_hub if shipment else None,
        "package_count": shipment.package_count if shipment else None,
        "package_weight_kg": shipment.package_weight_kg if shipment else None,
        "package_dimensions": shipment.package_dimensions if shipment else None,
        "packaged_at": packaged_at.isoformat() if packaged_at else None,
        "packaging_notes": shipment.packaging_notes if shipment else None,
        "subtotal": supplier_subtotal,
        "discount": supplier_discount,
        "vat": supplier_vat,
        "shipping": supplier_shipping,
        "total": supplier_total,
        "items": supplier_items,
    }


def upload_supplier_parcel_proof(
    order_id: int,
    file: UploadFile,
    notes: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    supplier_id = current_user["id"]
    supplier_items = (
        db.query(OrderItem)
        .join(Product)
        .filter(
            OrderItem.order_id == order_id,
            Product.supplier_id == supplier_id,
        )
        .all()
    )
    if not supplier_items:
        raise HTTPException(status_code=404, detail="Order not found or no products from this supplier")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order_status = str(getattr(order, "status", "pending"))
    if order_status not in {"processing", "prepared"}:
        raise HTTPException(
            status_code=409,
            detail="Packed parcel proof can only be uploaded while the order is being prepared for dispatch",
        )

    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .first()
    )
    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    pickup_location = next(
        (
            value for value in [
                getattr(supplier_profile, "address", None),
                getattr(supplier_profile, "city", None),
                getattr(supplier_profile, "region", None),
                getattr(supplier_profile, "country", None),
            ]
            if value
        ),
        None,
    )

    if shipment is None:
        shipment = Shipment(
            order_id=order.id,
            supplier_id=supplier_id,
            assigned_partner_id=None,
            status="processing",
            current_hub=pickup_location,
            packaged_at=utcnow(),
            packaged_by_user_id=supplier_id,
            packaging_notes=(notes or "").strip() or None,
            notes=(notes or "").strip() or None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        add_and_flush(db, shipment)
        ensure_shipment_identifiers(shipment)
    else:
        if pickup_location and not getattr(shipment, "current_hub", None):
            shipment.current_hub = pickup_location
        shipment.status = "processing"
        shipment.packaged_at = getattr(shipment, "packaged_at", None) or utcnow()
        shipment.packaged_by_user_id = supplier_id
        shipment.packaging_notes = (notes or "").strip() or getattr(shipment, "packaging_notes", None)
        shipment.updated_at = utcnow()
        ensure_shipment_identifiers(shipment)

    if not db.query(ShipmentEvent).filter(
        ShipmentEvent.shipment_id == shipment.id,
        ShipmentEvent.event_type.in_(["supplier_prepared", "picked_from_supplier"]),
    ).first():
        add_to_session(
            db,
            ShipmentEvent(
                shipment_id=shipment.id,
                order_id=shipment.order_id,
                supplier_id=shipment.supplier_id,
                actor_user_id=current_user["id"],
                actor_role=current_user.get("role", "supplier"),
                event_type="supplier_prepared",
                status_after="processing",
                distribution_channel=getattr(shipment, "distribution_channel", None),
                location=shipment.current_hub,
                scan_code=shipment.scan_code,
                notes=(notes or "").strip() or "Packed parcel proof uploaded by supplier",
                created_at=utcnow(),
            )
        )

    order.status = "prepared"
    order_shipments = db.query(Shipment).filter(Shipment.order_id == order.id).all()
    order.status = reconcile_order_status(order, order_shipments)

    partner_for_notification = getattr(shipment, "assigned_partner", None)
    if partner_for_notification and getattr(partner_for_notification, "user_id", None):
        stage_notification(
            db,
            user_id=partner_for_notification.user_id,
            type="shipment_update",
            title="Pickup Ready",
            message=f"Order #{order.id} is prepared for pickup{f' from {shipment.current_hub}' if shipment.current_hub else ''}.",
            link="/logistics-partner/shipments",
        )

    primary_item = supplier_items[0]
    image_url = _save_upload(file, supplier_id, db=db)
    media_base = os.path.basename(os.getenv("MEDIA_STORAGE_PATH", "uploads"))
    if image_url and not image_url.startswith(f"{media_base}/"):
        image_url = f"{media_base}/{image_url}"
    scan_code = shipment.scan_code if shipment and shipment.scan_code else f"ORDER-{order.id}"
    note_text = (notes or "").strip() or "Packed parcel proof uploaded by supplier"

    from controllers.product_verification_controller import create_verification

    verification = create_verification(
        {
            "product_id": primary_item.product_id,
            "order_id": order.id,
            "shipment_id": shipment.id if shipment else None,
            "verification_type": "supplier_dispatch",
            "result": "passed",
            "scan_code": scan_code,
            "image_urls": [image_url],
            "notes": note_text,
        },
        current_user,
        db,
    )
    commit_session(db)
    logistics_realtime_hub.publish(
        order_id=cast(int, getattr(shipment, "order_id")),
        payload={
            "type": "shipment.prepared",
            "shipment_id": cast(int, getattr(shipment, "id")),
            "order_id": cast(int, getattr(shipment, "order_id")),
            "assigned_partner_id": cast(Optional[int], getattr(shipment, "assigned_partner_id", None)),
            "status": "prepared",
            "tracking_number": cast(Optional[str], getattr(shipment, "tracking_number", None)),
            "current_hub": cast(Optional[str], getattr(shipment, "current_hub", None)),
            "scan_code": canonical_scan_code(shipment),
        },
        broadcast_all_partners=True,
    )
    return {
        **verification,
        "order_status": order.status,
        "shipment_status": "prepared" if shipment else None,
        "shipment_id": shipment.id if shipment else None,
        "assigned_partner_id": shipment.assigned_partner_id if shipment else None,
    }


# â”€â”€ Products â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_products(current_user: dict, db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    base_query = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    )
    total = base_query.count()
    query = base_query.order_by(Product.created_at.desc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    products = query.all()

    product_ids = [cast(int, product.id) for product in products]
    sales_rows = (
        db.query(
            OrderItem.product_id.label("product_id"),
            func.count(OrderItem.id).label("sales_count"),
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
        )
        .filter(OrderItem.product_id.in_(product_ids))
        .group_by(OrderItem.product_id)
        .all()
    ) if product_ids else []
    sales_map = {
        cast(int, row.product_id): {
            "sales_count": int(row.sales_count or 0),
            "revenue": float(row.revenue or 0),
        }
        for row in sales_rows
    }

    result = []
    for product in products:
        sales_data = sales_map.get(cast(int, product.id), {"sales_count": 0, "revenue": 0.0})

        result.append({
            **_build_supplier_product_payload(
                product,
                sales_count=int(sales_data["sales_count"]),
                revenue=float(sales_data["revenue"]),
            )
        })
    resolved_page_size = limit if limit is not None else len(result)
    return _build_list_page_payload(result, total, offset=offset, page_size=resolved_page_size)


def get_supplier_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    sales_data = db.query(
        func.count(OrderItem.id).label("sales_count"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).filter(OrderItem.product_id == product.id).first()

    return _build_supplier_product_payload(
        product,
        sales_count=sales_data.sales_count or 0,
        revenue=float(sales_data.revenue or 0),
    )


def _save_upload(file: UploadFile, supplier_id: int, country_code: str = None, product_id: int = None, db: Session = None) -> str:
    """Save an uploaded product media file using hierarchical path structure."""
    from services.media_service import save_product_media
    return save_product_media(file, db=db, supplier_id=supplier_id, country_code=country_code, product_id=product_id or 0, is_main=False)


def _save_supplier_profile_media_upload(file: UploadFile, supplier_id: int, field: str, country_code: str = None, db: Session = None) -> str:
    """Save supplier profile media using hierarchical path structure."""
    from services.media_service import save_supplier_media
    return save_supplier_media(file, db=db, supplier_id=supplier_id, country_code=country_code, media_type=field.replace("_url", ""))


def _process_image_with_tools(data: bytes, tools: dict, bg_preset: Optional[str] = None) -> bytes:
    """Apply free image processing tools (magic_erase, smart_crop, rotate, auto_light, upscale).

    If ``bg_preset`` is set, the chosen background-removal preset is applied
    first (replacing the generic ``magic_erase`` tool to avoid double removal).
    """
    if not tools and not bg_preset:
        return data
    if bg_preset:
        try:
            from services.bg_removal_service import remove_background
            data = remove_background(data, strategy=bg_preset)
        except Exception as exc:
            logger.warning("bg_preset application failed, using original: %s", exc)
        tools = {k: v for k, v in tools.items() if k != "magic_erase"}
    enabled = [k for k, v in tools.items() if v]
    if not enabled:
        return data
    try:
        from services.free_image_tools import auto_process_image
        return auto_process_image(data, tools=enabled)
    except Exception as exc:
        logger.warning("Image processing failed: %s", exc)
        return data


async def process_product_image(
    image: UploadFile,
    generate_angles: bool,
    current_user: dict,
) -> dict:
    """
    AI image pipeline for a product photo:
      1. Remove background â†’ white background JPEG
      2. (optional) Generate 4 novel-angle views via zero123-plus

    Returns:
      {
        "bg_removed_url":  "uploads/supplier_X_bg_â€¦jpg",
        "angle_urls":      ["uploads/supplier_X_angle0_â€¦.jpg", â€¦],
        "angles_generated": 4,
                "bg_removed": true,
                "angles_notice": "..."
      }
    """
    from services import image_ai_service
    from services.storage import storage as _storage

    raw = image.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image file")

    uid = current_user["id"]

    # ── Step 1: background removal ──────────────────────────────────────────────
    original_bytes = raw
    bg_removed_bytes = image_ai_service.remove_background(raw)
    bg_was_removed = bg_removed_bytes != original_bytes

    bg_key = f"supplier_{uid}_bg_{uuid.uuid4().hex[:8]}.jpg"
    bg_url = _storage.save(bg_key, bg_removed_bytes, content_type="image/jpeg")

    # ── Step 2: multi-angle generation ───────────────────────────────────────────
    angle_urls: list = []
    angles_notice: Optional[str] = None
    if generate_angles:
        try:
            angle_list = image_ai_service.generate_angles(original_bytes)
            for i, angle_bytes in enumerate(angle_list):
                angle_key = f"supplier_{uid}_angle{i}_{uuid.uuid4().hex[:8]}.jpg"
                angle_url = _storage.save(angle_key, angle_bytes, content_type="image/jpeg")
                angle_urls.append(angle_url)
            if not angle_urls:
                angles_notice = "Real AI angle generation is unavailable right now. Background removal was applied, but no new product views were produced."
        except Exception as exc:
            logger.warning("Angle generation failed: %s", exc)
            angles_notice = "Real AI angle generation failed for this image. Background removal was applied, but no new product views were produced."

    return {
        "bg_removed_url": bg_url,
        "angle_urls": angle_urls,
        "angles_generated": len(angle_urls),
        "bg_removed": bg_was_removed,
        "angles_notice": angles_notice,
    }


async def create_supplier_product_upload(
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
    video: Optional[UploadFile],
    image: Optional[UploadFile],
    additional_images: List[UploadFile],
    current_user: dict,
    db: Session,
    video_url_link: Optional[str] = None,
    image_url_link: Optional[str] = None,    # Web URL alternative to file upload
    extra_image_urls: Optional[List[str]] = None,  # Web URLs for extra images
    variants_payload: Optional[object] = None,
    image_tools: Optional[dict] = None,
    bg_preset: Optional[str] = None,
) -> Product:
    """Full supplier upload: main image + up to 20 additional gallery media files + variant details.
    Gallery media can be provided as uploads or web URLs."""
    MAX_ADDITIONAL_IMAGES = 20

    # Pre-process image through free AI tools if any are enabled
    if image and image.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
        try:
            raw = image.file.read()
            processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
            from io import BytesIO
            from fastapi import UploadFile
            image.file = BytesIO(processed)
            image.file.seek(0)
        except Exception as exc:
            logger.warning("Image pre-processing failed, using original: %s", exc)
            image.file.seek(0)

    # Resolve main image: prefer file upload, fall back to web URL or local uploads/ path
    if image and image.filename:
        image_url = _save_upload(image, current_user["id"], db=db)
    elif image_url_link and image_url_link.strip().startswith(("http://", "https://", "uploads/")):
        image_url = image_url_link.strip()
    else:
        image_url = None

    if video and video.filename:
        video_url = _save_upload(video, current_user["id"], db=db)
    else:
        video_url = _normalize_product_video_reference(video_url_link)

    # Resolve gallery media: file uploads first, then URL entries
    extra_paths: list = []
    for extra_file in additional_images:
        try:
            if extra_file and extra_file.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
                try:
                    raw = extra_file.file.read()
                    processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
                    from io import BytesIO
                    extra_file.file = BytesIO(processed)
                    extra_file.file.seek(0)
                except Exception:
                    extra_file.file.seek(0)
            path = _save_upload(extra_file, current_user["id"], db=db)
            extra_paths.append(path)
        except Exception:
            pass  # skip invalid extra images
    # Append web URL extra images
    for url in (extra_image_urls or []):
        if url and url.strip().startswith(("http://", "https://")):
            extra_paths.append(url.strip())

    if len(extra_paths) > MAX_ADDITIONAL_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"A product can include up to {MAX_ADDITIONAL_IMAGES} gallery media items",
        )

    new_product = _persist_supplier_product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        subcategory=subcategory,
        color=color,
        brand=brand,
        tags=tags,
        sizes=sizes,
        materials=materials,
        visibility_regions=visibility_regions,
        weight=weight,
        dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        is_active=is_active,
        image_url=image_url,
        video_url=video_url,
        additional_media=extra_paths,
        ai_description=None,
        variants_payload=variants_payload,
        current_user=current_user,
        db=db,
    )
    commit_and_refresh(db, new_product)
    _bump_product_cache_version()
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPLOAD,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="product",
        resource_id=new_product.id,
        details={"name": new_product.name, "category": new_product.category},
        status="success",
    )
    return new_product

def create_supplier_product(
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
    subcategory: Optional[str],
    is_active: bool,
    image: Optional[UploadFile],
    current_user: dict,
    db: Session,
    color: Optional[str] = None,
    tags: Optional[str] = None,
    sizes: Optional[str] = None,
    materials: Optional[str] = None,
    visibility_regions: Optional[object] = None,
    weight: Optional[float] = None,
    dimensions: Optional[str] = None,
    compare_price: Optional[float] = None,
    discount_starts_at: Optional[datetime] = None,
    discount_ends_at: Optional[datetime] = None,
    return_window_days: Optional[int] = None,
    video_url: Optional[object] = None,
    video: Optional[UploadFile] = None,
    variants_payload: Optional[object] = None,
    additional_images: Optional[List[UploadFile]] = None,
    brand: Optional[str] = None,
    image_tools: Optional[dict] = None,
    bg_preset: Optional[str] = None,
    variant_axes: Optional[object] = None,
    extra_attributes: Optional[dict] = None,
) -> dict:
    # Pre-process main image through free AI tools
    if image and image.filename and (image_tools and any(v for v in image_tools.values()) or bg_preset):
        try:
            raw = image.file.read()
            processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
            from io import BytesIO
            image.file = BytesIO(processed)
            image.file.seek(0)
        except Exception as exc:
            logger.warning("Image pre-processing failed, using original: %s", exc)
            image.file.seek(0)

    image_url = _save_upload(image, current_user["id"], db=db) if image and image.filename else None
    # A recorded/uploaded video file is saved like an image and its stored path
    # is used directly (already validated as MP4/WebM by save_product_media).
    # A string reference (YouTube/Vimeo/MP4 URL) goes through link normalization.
    if video is not None and getattr(video, "filename", None):
        normalized_video_url = _save_upload(video, current_user["id"], db=db)
    else:
        normalized_video_url = _normalize_product_video_reference(video_url)
    extra_paths: list[str] = []
    for extra_file in additional_images or []:
        if extra_file and extra_file.filename:
            try:
                if image_tools and any(v for v in image_tools.values()) or bg_preset:
                    try:
                        raw = extra_file.file.read()
                        processed = _process_image_with_tools(raw, image_tools or {}, bg_preset=bg_preset)
                        from io import BytesIO
                        extra_file.file = BytesIO(processed)
                        extra_file.file.seek(0)
                    except Exception:
                        extra_file.file.seek(0)
                extra_paths.append(_save_upload(extra_file, current_user["id"], db=db))
            except Exception:
                continue

    new_product = _persist_supplier_product(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category=category,
        subcategory=subcategory,
        color=color,
        brand=brand,
        tags=tags,
        sizes=sizes,
        materials=materials,
        visibility_regions=visibility_regions,
        weight=weight,
        dimensions=dimensions,
        compare_price=compare_price,
        discount_starts_at=discount_starts_at,
        discount_ends_at=discount_ends_at,
        return_window_days=return_window_days,
        is_active=is_active,
        image_url=image_url,
        video_url=normalized_video_url,
        additional_media=extra_paths,
        ai_description=None,
        variants_payload=variants_payload,
        variant_axes=variant_axes,
        bg_preset=bg_preset,
        extra_attributes=extra_attributes,
        current_user=current_user,
        db=db,
    )
    commit_and_refresh(db, new_product)
    _bump_product_cache_version()

    return _build_supplier_product_payload(new_product)


def update_supplier_product(
    product_id: int,
    name: Optional[str],
    description: Optional[str],
    price: Optional[float],
    stock_quantity: Optional[int],
    category: Optional[str],
    subcategory: Optional[str],
    is_active: Optional[bool],
    image: Optional[UploadFile],
    current_user: dict,
    db: Session,
    color: Optional[str] = None,
    tags: Optional[str] = None,
    sizes: Optional[str] = None,
    materials: Optional[str] = None,
    visibility_regions: object = _UNSET,
    weight: Optional[float] = None,
    dimensions: Optional[str] = None,
    compare_price: object = _UNSET,
    discount_starts_at: object = _UNSET,
    discount_ends_at: object = _UNSET,
    return_window_days: object = _UNSET,
    video_url: object = _UNSET,
    variants_payload: object = _UNSET,
    is_new: object = _UNSET,
    additional_images: Optional[List[UploadFile]] = None,
) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if image:
        file_path = _save_upload(image, current_user["id"], db=db)
        if product.image_url and os.path.exists(product.image_url):
            os.remove(product.image_url)
        product.image_url = file_path

    if additional_images:
        existing_media: list[str] = []
        if product.images:
            try:
                parsed_media = json.loads(product.images) if isinstance(product.images, str) else product.images
                if isinstance(parsed_media, list):
                    existing_media = [str(item).strip() for item in parsed_media if str(item).strip()]
            except (json.JSONDecodeError, TypeError):
                existing_media = []

        appended_media = existing_media[:]
        for media_file in additional_images:
            if media_file and media_file.filename:
                appended_media.append(_save_upload(media_file, current_user["id"], db=db))
        product.images = json.dumps(appended_media) if appended_media else None

    if name is not None:
        product.name = html.escape(name.strip())
    if description is not None:
        product.description = html.escape(description)
    if price is not None:
        product.price = price
    if stock_quantity is not None:
        product.stock = stock_quantity
    if category is not None:
        product.category = category
    if subcategory is not None:
        product.subcategory = _normalize_optional_product_text(subcategory)
    if color is not None:
        product.color = color
    if is_active is not None:
        product.is_active = is_active
    if tags is not None:
        product.tags = tags
    if sizes is not None:
        product.sizes = sizes
    if materials is not None:
        product.materials = materials
    if visibility_regions is not _UNSET:
        normalized_visibility_regions = _normalize_product_visibility_regions(visibility_regions)
        product.visibility_regions = json.dumps(normalized_visibility_regions) if normalized_visibility_regions else None
    if weight is not None:
        product.weight = weight
    if dimensions is not None:
        product.dimensions = dimensions
    if compare_price is not _UNSET:
        product.compare_price = compare_price
    if discount_starts_at is not _UNSET:
        product.discount_starts_at = discount_starts_at
    if discount_ends_at is not _UNSET:
        product.discount_ends_at = discount_ends_at
    if return_window_days is not _UNSET:
        product.return_window_days = _parse_supplier_return_window_days(
            return_window_days,
            supplier_id=current_user["id"],
            db=db,
        )
    if is_new is not _UNSET:
        product.is_new = is_new
    if variants_payload is not _UNSET:
        _replace_product_variants(product, _parse_product_variants_payload(variants_payload), db)

    commit_and_refresh(db, product)
    _bump_product_cache_version()

    return _build_supplier_product_payload(product)


def delete_supplier_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_deleted = True
    commit_session(db)
    _bump_product_cache_version()
    return {"message": "Product deleted successfully"}


# â”€â”€ Analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_analytics(period: str, current_user: dict, db: Session) -> dict:
    day_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = day_map.get(period, 30)

    start_date = utcnow() - timedelta(days=days)
    previous_start_date = start_date - timedelta(days=days)
    sid = current_user["id"]

    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).scalar() or 0

    total_orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).distinct().count()

    total_products = db.query(Product).filter(Product.supplier_id == sid).count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    prev_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= previous_start_date,
        Order.created_at < start_date,
    ).scalar() or 0

    prev_orders = db.query(Order).join(OrderItem).join(Product).filter(
        Product.supplier_id == sid,
        Order.created_at >= previous_start_date,
        Order.created_at < start_date,
    ).distinct().count()

    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    order_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0

    # Single grouped query replaces N+1 per-day queries
    daily_rows = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem, OrderItem.order_id == Order.id).join(Product, Product.id == OrderItem.product_id).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).group_by(func.date(Order.created_at)).all()
    revenue_by_date = {str(row.date): float(row.revenue) for row in daily_rows}
    daily_revenue = [
        {
            "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "revenue": revenue_by_date.get(
                (start_date + timedelta(days=i)).strftime("%Y-%m-%d"), 0.0
            ),
        }
        for i in range(days)
    ]

    top_selling = db.query(
        Product.id,
        Product.name,
        Product.image_url,
        func.count(OrderItem.id).label("sales"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem).join(Order).filter(
        Product.supplier_id == sid,
        Order.created_at >= start_date,
    ).group_by(Product.id, Product.name, Product.image_url).order_by(
        func.sum(OrderItem.price * OrderItem.quantity).desc()
    ).limit(10).all()

    product_performance = []
    for product in db.query(Product).filter(Product.supplier_id == sid).limit(10).all():
        sales_data = db.query(
            func.count(OrderItem.id),
            func.sum(OrderItem.price * OrderItem.quantity),
        ).filter(OrderItem.product_id == product.id).first()
        views = (sales_data[0] or 0) * 10 + 50
        purchases = sales_data[0] or 0
        conversion = (purchases / views * 100) if views > 0 else 0
        product_performance.append({
            "id": product.id,
            "name": product.name,
            "views": views,
            "purchases": purchases,
            "conversion": conversion,
        })

    total_views = sum(p["views"] for p in product_performance)
    conversion_rate = (total_orders / total_views * 100) if total_views > 0 else 0

    return {
        "overview": {
            "totalRevenue": float(total_revenue),
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "averageOrderValue": float(avg_order_value),
            "conversionRate": conversion_rate,
        },
        "revenue": {"daily": daily_revenue, "monthly": [], "yearly": []},
        "products": {
            "topSelling": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sales": p.sales,
                    "revenue": float(p.revenue),
                    "image_url": p.image_url,
                }
                for p in top_selling
            ],
            "performance": product_performance,
        },
        "trends": {
            "revenueGrowth": revenue_growth,
            "orderGrowth": order_growth,
            "customerGrowth": 0,
            "period": period,
        },
    }


# â”€â”€ Inventory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_inventory(current_user: dict, db: Session) -> list:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).all()
    result = []
    for product in products:
        thirty_days_ago = utcnow() - timedelta(days=30)
        sales_data = db.query(
            func.sum(OrderItem.quantity).label("total_sold"),
            func.count(OrderItem.id).label("order_count"),
        ).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= thirty_days_ago,
        ).first()

        total_sold = sales_data.total_sold or 0
        sales_velocity = total_sold / 30.0
        reorder_point = int(sales_velocity * 7)

        result.append({
            "id": product.id,
            "name": product.name,
            "current_stock": product.stock,
            "minimum_stock": max(reorder_point, 5),
            "maximum_stock": max(reorder_point * 3, 50),
            "category": product.category or "General",
            "supplier_price": product.price,
            "last_updated": (product.updated_at or product.created_at).isoformat(),
            "sales_velocity": sales_velocity,
            "reorder_point": reorder_point,
        })
    return result


def update_product_stock(product_id: int, stock_update: dict, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or doesn't belong to this supplier")
    new_stock = stock_update.get("stock_quantity", product.stock)
    if new_stock is None or new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative")
    product.stock = int(new_stock)
    commit_and_refresh(db, product)
    _bump_product_cache_version()
    return {"message": "Stock updated successfully", "product": {"id": product.id, "name": product.name, "stock": product.stock}}


def update_inventory_levels(product_id: int, levels_update: dict, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or doesn't belong to this supplier")
    min_stock = levels_update.get("minimum_stock")
    max_stock = levels_update.get("maximum_stock")
    if min_stock is not None and min_stock < 0:
        raise HTTPException(status_code=400, detail="Minimum stock cannot be negative")
    if max_stock is not None and max_stock < 0:
        raise HTTPException(status_code=400, detail="Maximum stock cannot be negative")
    if min_stock is not None and max_stock is not None and min_stock > max_stock:
        raise HTTPException(status_code=400, detail="Minimum stock cannot be greater than maximum stock")
    if min_stock is not None:
        product.minimum_stock = int(min_stock)
    if max_stock is not None:
        product.maximum_stock = int(max_stock)
    if min_stock is not None or max_stock is not None:
        commit_and_refresh(db, product)
        _bump_product_cache_version()
    return {"message": "Inventory levels updated successfully", "minimum_stock": product.minimum_stock, "maximum_stock": product.maximum_stock}


def get_inventory_alerts(current_user: dict, db: Session) -> dict:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).all()
    alerts = []
    for product in products:
        thirty_days_ago = utcnow() - timedelta(days=30)
        sales_data = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= thirty_days_ago,
        ).scalar() or 0

        sales_velocity = sales_data / 30.0
        reorder_point = int(sales_velocity * 7)

        if product.stock <= reorder_point and product.stock > 0:
            alerts.append({
                "type": "low_stock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Low stock alert: {product.name} has {product.stock} units remaining",
            })
        elif product.stock == 0:
            alerts.append({
                "type": "out_of_stock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": 0,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Out of stock: {product.name} needs restocking",
            })
        elif product.stock > reorder_point * 3:
            alerts.append({
                "type": "overstock",
                "product_id": product.id,
                "product_name": product.name,
                "current_stock": product.stock,
                "reorder_point": reorder_point,
                "sales_velocity": sales_velocity,
                "message": f"Overstock alert: {product.name} has excess inventory ({product.stock} units)",
            })

    return {"alerts": alerts, "total_alerts": len(alerts)}


# â”€â”€ Profile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_profile(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()

    total_products = db.query(Product).filter(Product.supplier_id == current_user["id"]).count()
    total_orders = (
        db.query(Order).join(OrderItem).join(Product)
        .filter(Product.supplier_id == current_user["id"])
        .distinct()
        .count()
    )
    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).join(Product).filter(
        Product.supplier_id == current_user["id"],
        Order.status == "completed",
    ).scalar() or 0

    return {
        "id": supplier.id,
        "username": supplier.username,
        "email": supplier.email,
        "phone": supplier.phone,
        "business_name": profile.business_name if profile else None,
        "business_address": profile.address if profile else None,
        "website": profile.website if profile else None,
        "bio": profile.bio if profile else None,
        "about_us": getattr(profile, "about_us", None) if profile else None,
        "verification_status": profile.verification_status if profile else "pending",
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "created_at": supplier.created_at.isoformat(),
    }


def update_supplier_profile(profile_update: dict, current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")

    if "phone" in profile_update:
        supplier.phone = _sanitize_profile_string(profile_update.get("phone"))

    profile_field_map = {
        "business_name": "business_name",
        "business_address": "address",
        "website": "website",
        "bio": "bio",
        "about_us": "about_us",
        "business_type": "business_type",
    }
    for source_field, target_field in profile_field_map.items():
        if source_field not in profile_update:
            continue
        value = profile_update.get(source_field)
        if target_field == "website" and isinstance(value, str) and value.strip() and not value.startswith(("http://", "https://")):
            value = f"https://{value.strip()}"
        setattr(profile, target_field, _sanitize_profile_string(value))

    if "established_year" in profile_update:
        raw_year = profile_update.get("established_year")
        if raw_year in (None, ""):
            profile.established_year = None
        else:
            try:
                profile.established_year = int(raw_year)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Established year must be a number") from exc

    commit_and_refresh(db, supplier)
    return get_supplier_profile(current_user, db)


def request_verification(current_user: dict, db: Session) -> dict:
    supplier = db.query(User).filter(User.id == current_user["id"]).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")

    if profile.verification_status in (None, "pending"):
        profile.verification_status = "under_review"
    commit_session(db)
    return {"message": "Verification request submitted successfully", "status": profile.verification_status or "pending"}


# â”€â”€ Payouts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_payout_history(current_user: dict, db: Session) -> list:
    payouts = (
        db.query(Payout)
        .filter(Payout.supplier_id == current_user["id"])
        .order_by(Payout.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "amount": p.amount,
            "status": p.status,
            "method": p.method,
            "reference": p.reference_id,
            "notes": p.notes,
            "created_at": p.created_at.isoformat(),
            "processed_at": p.processed_at.isoformat() if p.processed_at else None,
        }
        for p in payouts
    ]


def get_supplier_shipments(current_user: dict, db: Session) -> list:
    """Compatibility endpoint for mobile supplier logistics list."""
    supplier_id = current_user["id"]
    shipments = (
        db.query(Shipment)
        .filter(Shipment.supplier_id == supplier_id)
        .order_by(Shipment.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "order_id": s.order_id,
            "tracking_number": s.tracking_number,
            "carrier": s.carrier_name or (s.carrier.name if s.carrier else None),
            "status": s.status,
            "distribution_channel": s.distribution_channel,
            "current_hub": s.current_hub,
            "scan_code": s.scan_code,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in shipments
    ]


def request_payout(body: dict, current_user: dict, db: Session) -> dict:
    amount = body.get("amount")
    method = body.get("method", "bank")
    notes = body.get("notes")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=422, detail="Amount must be positive")
    payout = create_supplier_payout_request(
        db,
        supplier_id=current_user["id"],
        amount=float(amount),
        method=method,
        notes=notes,
        country_code=current_user.get("country_code") or current_user.get("preferred_country") or None,
    )
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_REQUESTED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="payout",
        resource_id=payout.id,
        details={"amount": float(amount), "method": method},
    )
    return {
        "id": payout.id,
        "status": payout.status,
        "amount": payout.amount,
        "method": payout.method,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "created_at": payout.created_at.isoformat() if payout.created_at else None,
        "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
    }


# â”€â”€ Bulk Operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def execute_bulk_operation(operation: dict, current_user: dict, db: Session) -> dict:
    operation_type = operation.get("type")
    product_ids = operation.get("productIds", [])
    value = operation.get("value")

    if not product_ids:
        raise HTTPException(status_code=400, detail="No products selected")

    products = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.supplier_id == current_user["id"],
    ).all()
    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="Some products not found or don't belong to this supplier")

    updated_count = 0
    if operation_type == "price_update":
        if value is None or value < 0:
            raise HTTPException(status_code=400, detail="Invalid price value")
        for product in products:
            product.price = float(value)
        updated_count = len(products)
    elif operation_type == "category_change":
        if not value or not isinstance(value, str):
            raise HTTPException(status_code=400, detail="Invalid category value")
        for product in products:
            product.category = value
        updated_count = len(products)
    elif operation_type == "stock_update":
        if value is None or value < 0:
            raise HTTPException(status_code=400, detail="Invalid stock value")
        for product in products:
            product.stock = int(value)
        updated_count = len(products)
    elif operation_type == "status_change":
        # value may be bool, 0/1, "active"/"inactive"
        if value is None:
            raise HTTPException(status_code=400, detail="value is required for status_change (true/false or 'active'/'inactive')")
        if isinstance(value, bool):
            target_active = value
        elif isinstance(value, (int, float)):
            target_active = bool(value)
        elif isinstance(value, str):
            if value.lower() in ("true", "active", "1"):
                target_active = True
            elif value.lower() in ("false", "inactive", "0"):
                target_active = False
            else:
                raise HTTPException(status_code=400, detail="value must be true/false or 'active'/'inactive'")
        else:
            raise HTTPException(status_code=400, detail="Invalid value for status_change")
        for product in products:
            product.is_active = target_active
        updated_count = len(products)
    elif operation_type == "delete":
        for product in products:
            product.is_deleted = True
        updated_count = len(products)
    else:
        raise HTTPException(status_code=400, detail="Invalid operation type")

    commit_session(db)
    _bump_product_cache_version()
    return {
        "message": f"Bulk {operation_type.replace('_', ' ')} completed successfully",
        "updated_count": updated_count,
        "operation_type": operation_type,
    }


def bulk_inventory_adjust(adjustments: list, current_user: dict, db: Session) -> dict:
    """Bulk adjust stock for multiple products in one request.

    Each entry in `adjustments` must be:
        {"product_id": int, "mode": "set" | "adjust", "value": int}

    ``mode="set"``    â†’ set stock to exactly `value` (must be >= 0).
    ``mode="adjust"`` â†’ add/subtract `value` from current stock (result clamped to 0).
    """
    if current_user["role"] not in ("supplier", "admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    if not adjustments:
        raise HTTPException(status_code=400, detail="No adjustments provided")
    if len(adjustments) > 200:
        raise HTTPException(status_code=400, detail="Cannot adjust more than 200 products at once")

    product_ids = []
    for entry in adjustments:
        pid = entry.get("product_id")
        if not isinstance(pid, int) or pid <= 0:
            raise HTTPException(status_code=422, detail=f"Invalid product_id: {pid}")
        product_ids.append(pid)

    products_map: dict[int, Product] = {
        cast(int, p.id): p
        for p in db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.supplier_id == current_user["id"],
            Product.is_deleted == False,  # noqa: E712
        ).all()
    }

    updated: list[dict] = []
    skipped: list[dict] = []

    for entry in adjustments:
        pid = int(entry["product_id"])
        mode = str(entry.get("mode", "set")).lower()
        raw_value = entry.get("value")

        product = products_map.get(pid)
        if not product:
            skipped.append({"product_id": pid, "reason": "Not found or not owned by this supplier"})
            continue

        try:
            delta = int(raw_value)
        except (TypeError, ValueError):
            skipped.append({"product_id": pid, "reason": f"Invalid value: {raw_value}"})
            continue

        if mode == "set":
            if delta < 0:
                skipped.append({"product_id": pid, "reason": "Stock cannot be set to a negative value"})
                continue
            old_stock = int(product.stock or 0)
            product.stock = delta
        elif mode == "adjust":
            old_stock = int(product.stock or 0)
            new_stock = max(0, old_stock + delta)
            product.stock = new_stock
        else:
            skipped.append({"product_id": pid, "reason": f"Unknown mode '{mode}'. Use 'set' or 'adjust'"})
            continue

        updated.append({
            "product_id": pid,
            "product_name": product.name,
            "old_stock": old_stock,
            "new_stock": product.stock,
            "mode": mode,
        })

    if updated:
        commit_session(db)
        _bump_product_cache_version()
        audit_log(
            db=db,
            action=AuditAction.PRODUCT_UPDATE,
            user_id=current_user["id"],
            username=current_user["username"],
            user_role=current_user["role"],
            resource_type="product",
            resource_id=0,
            details={"bulk_stock_adjust": True, "count": len(updated), "adjustments": updated},
        )
    return {
        "updated": len(updated),
        "skipped": len(skipped),
        "details": updated,
        "skipped_details": skipped,
    }


def export_products_csv(current_user: dict, db: Session) -> StreamingResponse:
    products = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Description", "Price", "Stock Quantity", "Category", "Status", "Image URL", "Created At"])
    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.description or "",
            product.price,
            product.stock,
            product.category or "",
            "active",
            product.image_url or "",
            product.created_at.isoformat() if product.created_at else "",
        ])
    csv_content = output.getvalue()
    output.close()

    def iter_csv():
        yield csv_content

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_export.csv"},
    )


async def import_products_csv(file: UploadFile, current_user: dict, db: Session) -> dict:
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    content = await file.read()
    from utils.file_validation import validate_csv_bytes
    validate_csv_bytes(content, file.filename or "")
    csv_content = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    imported_count = 0
    errors = []

    for row_num, row in enumerate(csv_reader, start=2):
        try:
            if not row.get("Name"):
                errors.append(f"Row {row_num}: Missing product name")
                continue
            if not row.get("Price"):
                errors.append(f"Row {row_num}: Missing price")
                continue
            raw_name = row["Name"].strip()
            raw_desc = row.get("Description", "").strip()
            raw_cat = row.get("Category", "").strip()
            # Generate unique slug for the product
            slug_base = re.sub(r"[^a-z0-9]+", "-", raw_name.lower()).strip("-") or "product"
            product_slug = slug_base
            attempt = 0
            while db.query(Product).filter(Product.slug == product_slug).first():
                attempt += 1
                product_slug = f"{slug_base}-{attempt}"
            new_product = Product(
                name=html.escape(raw_name),
                slug=product_slug,
                description=html.escape(raw_desc) if raw_desc else None,
                price=float(row["Price"]),
                stock=int(row.get("Stock Quantity", 0)),
                category=html.escape(raw_cat) if raw_cat else None,
                image_url=None,  # never accept image_url from CSV (SSRF risk)
                supplier_id=current_user["id"],
            )
            add_to_session(db, new_product)
            imported_count += 1
        except ValueError as e:
            errors.append(f"Row {row_num}: Invalid data - {str(e)}")
        except Exception as e:
            errors.append(f"Row {row_num}: Error - {str(e)}")

    commit_session(db)
    if imported_count:
        _bump_product_cache_version()
    return {
        "message": f"Import completed. {imported_count} products imported successfully.",
        "imported_count": imported_count,
        "errors": errors,
    }


# â”€â”€ Reports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_reports(period: str, current_user: dict, db: Session) -> dict:
    now = utcnow()
    day_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = day_map.get(period, 30)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)

    supplier_products = db.query(Product).filter(Product.supplier_id == current_user["id"]).all()
    product_ids = [p.id for p in supplier_products]

    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    total_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    total_products = len(supplier_products)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    conversion_rate = (total_orders / total_products * 100) if total_products > 0 else 0

    revenue_trends = db.query(
        func.date(Order.created_at).label("date"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()

    top_products = db.query(
        Product.name,
        Product.id,
        Product.image_url,
        func.sum(OrderItem.quantity).label("sales"),
        func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
    ).join(OrderItem).join(Order).filter(
        Product.supplier_id == current_user["id"],
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).group_by(Product.id, Product.name, Product.image_url).order_by(
        func.sum(OrderItem.price * OrderItem.quantity).desc()
    ).limit(10).all()

    product_performance = []
    for product in supplier_products[:10]:
        purchases = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.product_id == product.id,
            Order.created_at >= start_date,
            Order.status.in_(["completed", "shipped", "delivered"]),
        ).scalar() or 0
        views = purchases * 2
        conversion = (purchases / views * 100) if views > 0 else 0
        product_performance.append({
            "id": product.id,
            "name": product.name,
            "views": views,
            "purchases": purchases,
            "conversion": conversion,
        })

    prev_period_start = start_date - (now - start_date)
    prev_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    prev_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    order_growth = ((total_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0

    current_customers = db.query(func.count(func.distinct(Order.user_id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    prev_customers = db.query(func.count(func.distinct(Order.user_id))).join(OrderItem).filter(
        OrderItem.product_id.in_(product_ids),
        Order.created_at >= prev_period_start,
        Order.created_at < start_date,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    customer_growth = ((current_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else 0

    return {
        "overview": {
            "totalRevenue": float(total_revenue),
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "averageOrderValue": float(avg_order_value),
            "conversionRate": float(conversion_rate),
        },
        "revenue": {
            "daily": [{"date": str(r.date), "revenue": float(r.revenue)} for r in revenue_trends],
            "monthly": [],
            "yearly": [],
        },
        "products": {
            "topSelling": [
                {"id": p.id, "name": p.name, "sales": p.sales, "revenue": float(p.revenue), "image_url": p.image_url}
                for p in top_products
            ],
            "performance": product_performance,
        },
        "trends": {
            "revenueGrowth": float(revenue_growth),
            "orderGrowth": float(order_growth),
            "customerGrowth": float(customer_growth),
            "period": period,
        },
        "aiAudit": _load_supplier_ai_audit_summary(),
    }


# â”€â”€ Bulk Image/Details Upload â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BULK_PRODUCTS = 50
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


async def bulk_upload_products(
    products_json: str,
    images: List[UploadFile],
    use_ai: bool,
    current_user: dict,
    db: Session,
) -> dict:
    """
    Bulk-create multiple products at once, with optional AI enrichment.

    products_json: JSON array string of product objects.
      Each object: { name, price, stock, category?, description?, brand?, color? }
    images: list of UploadFile â€” matched to products by filename or index
      (filename should match product name or be indexed p0.jpg, p1.jpg â€¦)
    use_ai: if True, call AI service to suggest category, tags, and description
            for each product that does not already have them.
    """
    # â”€â”€ parse product list â”€â”€
    try:
        raw_products: list = json.loads(products_json)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="products_json must be a valid JSON array")

    if not isinstance(raw_products, list) or not raw_products:
        raise HTTPException(status_code=400, detail="products_json must be a non-empty JSON array")

    if len(raw_products) > MAX_BULK_PRODUCTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BULK_PRODUCTS} products per bulk upload",
        )

    # â”€â”€ build upload map (filename â†’ content metadata) â”€â”€
    from utils.file_validation import VIDEO_EXTENSIONS, _sniff_image_type, validate_upload_video

    upload_map: dict[str, dict[str, object]] = {}
    primary_image_keys: list[str] = []
    for img in images:
        if not img or not img.filename:
            continue
        ext = os.path.splitext(img.filename)[1].lower()
        is_video = ext in VIDEO_EXTENSIONS or (img.content_type or "").startswith("video/")
        if ext not in ALLOWED_IMAGE_EXTS and not is_video:
            continue
        content = img.file.read()
        if len(content) > (25 * 1024 * 1024 if is_video else MAX_IMAGE_SIZE):
            continue  # skip oversized images silently; will log
        if is_video:
            try:
                normalized_ext = validate_upload_video(content, img.filename or "bulk-media.mp4")
            except HTTPException:
                continue
        else:
            # Reject files that don't match a known image magic signature
            if _sniff_image_type(content) is None:
                continue
            normalized_ext = ext or ".jpg"
        key = img.filename.lower()
        upload_map[key] = {"content": content, "ext": normalized_ext, "is_video": is_video}
        if not is_video:
            primary_image_keys.append(key)

    created: list[dict] = []
    errors: list[dict] = []

    for idx, item in enumerate(raw_products):
        if not isinstance(item, dict):
            errors.append(_build_bulk_upload_error(idx, "Item must be an object"))
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            errors.append(_build_bulk_upload_error(idx, "name is required"))
            continue

        try:
            price = float(item.get("price", 0))
        except (TypeError, ValueError):
            errors.append(_build_bulk_upload_error(idx, "price must be a number", name=name))
            continue

        if price <= 0:
            errors.append(_build_bulk_upload_error(idx, "price must be > 0", name=name))
            continue

        try:
            stock = int(item.get("stock", 0))
        except (TypeError, ValueError):
            stock = 0

        description = html.escape(str(item.get("description", "")).strip())
        category = str(item.get("category", "")).strip()
        subcategory = _normalize_optional_product_text(item.get("subcategory", item.get("sub_category")))
        brand = str(item.get("brand", "")).strip() or None
        color = str(item.get("color", "")).strip() or None
        raw_tags = item.get("tags", "")
        tags_str = (", ".join(raw_tags) if isinstance(raw_tags, list) else str(raw_tags)).strip() or None
        # Variant / spec fields
        sizes_val = item.get("sizes")
        sizes_str: Optional[str] = json.dumps(sizes_val) if isinstance(sizes_val, list) else (str(sizes_val) if sizes_val else None)
        materials_str: Optional[str] = str(item.get("materials", "")).strip() or None
        weight_val = item.get("weight")
        try:
            weight_float: Optional[float] = float(weight_val) if weight_val else None
        except (TypeError, ValueError):
            weight_float = None
        dimensions_str: Optional[str] = str(item.get("dimensions", "")).strip() or None
        normalized_visibility_regions = _normalize_product_visibility_regions(item.get("visibility_regions"))
        compare_price_value = item.get("compare_price", item.get("discount_price"))
        try:
            compare_price_float: Optional[float] = float(compare_price_value) if compare_price_value not in (None, "") else None
        except (TypeError, ValueError):
            errors.append(_build_bulk_upload_error(idx, "compare_price must be a number", name=name))
            continue
        try:
            discount_starts_at_value = _parse_optional_datetime(item.get("discount_starts_at"))
            discount_ends_at_value = _parse_optional_datetime(item.get("discount_ends_at"))
            return_window_days_value = _parse_supplier_return_window_days(
                item.get("return_window_days"),
                supplier_id=current_user["id"],
                db=db,
            )
            video_url_value = _normalize_product_video_reference(item.get("video_url"))
            parsed_variants = _parse_product_variants_payload(item.get("variants"))
        except HTTPException as exc:
            errors.append(_build_bulk_upload_error(idx, exc.detail, name=name))
            continue
        is_active = _coerce_optional_bool(item.get("is_active"), True)
        # Web URL or server-relative path for main image (alternative to file upload)
        item_image_url: Optional[str] = str(item.get("image_url", "")).strip() or None
        if item_image_url and not item_image_url.startswith(("http://", "https://", "uploads/")):
            item_image_url = None
        # Additional image URLs â€” accept full http(s) URLs or server-relative "uploads/" paths
        extra_urls_raw = item.get("additional_image_urls", [])
        extra_url_list: list = [
            u for u in (extra_urls_raw if isinstance(extra_urls_raw, list) else [])
            if isinstance(u, str) and (u.startswith(("http://", "https://")) or u.startswith("uploads/"))
        ]

        from services.storage import storage as _storage

        # Extra image files uploaded with naming convention p{idx}_e{i}.ext
        for extra_i in range(19):
            for ext_try in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"]:
                ekey = f"p{idx}_e{extra_i}{ext_try}"
                entry = upload_map.get(ekey)
                if entry:
                    try:
                        saved_ext = str(entry["ext"])
                        efname = f"{uuid.uuid4().hex}{saved_ext}"
                        extra_url = _storage.save(efname, entry["content"])
                        extra_url_list.append(extra_url)
                    except Exception as exc:
                        logger.warning("Failed to save extra image %s: %s", ekey, exc)
                    break  # found this slot, move to next index

        for video_ext in [".mp4", ".webm"]:
            video_key = f"p{idx}_video{video_ext}"
            video_entry = upload_map.get(video_key)
            if not video_entry:
                continue
            try:
                saved_ext = str(video_entry["ext"])
                video_filename = f"{uuid.uuid4().hex}{saved_ext}"
                video_url_value = _storage.save(video_filename, video_entry["content"])
            except Exception as exc:
                logger.warning("Failed to save product video %s: %s", video_key, exc)
            break

        for variant_index, variant_payload in enumerate(parsed_variants):
            if variant_payload.get("media_url"):
                continue
            for media_ext in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"]:
                media_key = f"p{idx}_v{variant_index}{media_ext}"
                media_entry = upload_map.get(media_key)
                if not media_entry:
                    continue
                try:
                    saved_ext = str(media_entry["ext"])
                    variant_filename = f"{uuid.uuid4().hex}{saved_ext}"
                    variant_payload["media_url"] = _storage.save(variant_filename, media_entry["content"])
                except Exception as exc:
                    logger.warning("Failed to save variant media %s: %s", media_key, exc)
                break

        # â”€â”€ resolve image for this product â”€â”€
        img_bytes: Optional[bytes] = None
        matched_image_key: Optional[str] = None
        # Try: index key p0.jpg/p1.jpg, then name-based match, then position
        for key in [f"p{idx}.jpg", f"p{idx}.jpeg", f"p{idx}.png", f"p{idx}.webp",
                    f"{name.lower().replace(' ', '_')}.jpg",
                    f"{name.lower().replace(' ', '_')}.jpeg",
                    f"{name.lower().replace(' ', '_')}.png",
                    f"{name.lower().replace(' ', '_')}.webp"]:
            entry = upload_map.get(key)
            if entry and not bool(entry["is_video"]):
                img_bytes = entry["content"]
                matched_image_key = key
                break
        # positional fallback â€” only when no URL was supplied for this product
        if img_bytes is None and item_image_url is None and idx < len(primary_image_keys):
            matched_image_key = primary_image_keys[idx]
            img_bytes = upload_map[matched_image_key]["content"]

        # â”€â”€ AI enrichment â”€â”€
        ai_description: Optional[str] = None
        if use_ai:
            try:
                suggested_cat = ai_service.suggest_category(name, description)
                if not category:
                    category = suggested_cat
                suggested_tags = ai_service.suggest_tags(name, category, description)
                if not tags_str:
                    tags_str = ", ".join(suggested_tags)
                ai_description = ai_service.generate_product_description(
                    name=name, category=category, image_bytes=img_bytes
                )
                if not description:
                    description = ai_description
            except Exception as exc:
                logger.warning("AI enrichment failed for product %r: %s", name, exc)

        # â”€â”€ save image file â”€â”€
        image_url: Optional[str] = None
        if img_bytes:
            try:
                ext = ".jpg"
                if matched_image_key:
                    ext = str(upload_map[matched_image_key]["ext"])
                filename = f"{uuid.uuid4().hex}{ext}"
                image_url = _storage.save(filename, img_bytes)
            except Exception as exc:
                logger.warning("Failed to save image for %r: %s", name, exc)
        # Fall back to web URL if no file image was saved
        if not image_url and item_image_url:
            image_url = item_image_url

        # Merge file-uploaded extra images from image_map with extra URL list
        additional_images_combined: list = list(extra_url_list)

        # â”€â”€ create product â”€â”€
        try:
            product = _persist_supplier_product(
                name=name,
                description=description or "",
                price=round(price, 2),
                stock_quantity=max(0, stock),
                category=category or "General",
                subcategory=subcategory,
                color=color,
                brand=brand,
                tags=tags_str,
                sizes=sizes_str,
                materials=materials_str,
                visibility_regions=normalized_visibility_regions,
                weight=weight_float,
                dimensions=dimensions_str,
                compare_price=compare_price_float,
                discount_starts_at=discount_starts_at_value,
                discount_ends_at=discount_ends_at_value,
                return_window_days=return_window_days_value,
                is_active=is_active,
                image_url=image_url,
                video_url=video_url_value,
                additional_media=additional_images_combined,
                ai_description=ai_description,
                variants_payload=parsed_variants,
                current_user=current_user,
                db=db,
            )
            created.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
                "subcategory": product.subcategory,
                "tags": product.tags,
                "ai_description": product.ai_description,
                "image_url": product.image_url,
                "video_url": product.videos[0].video_url if product.videos else None,
                "visibility_regions": _serialize_product_visibility_regions(product.visibility_regions),
                "variants": [_serialize_product_variant(variant, product.price) for variant in (product.variants or [])],
            })
        except HTTPException as exc:
            logger.warning("Bulk upload validation failed for %r: %s", name, exc.detail)
            errors.append(_build_bulk_upload_error(idx, exc.detail, name=name))
        except Exception as exc:
            logger.error("Failed to create product %r: %s", name, exc)
            errors.append(_build_bulk_upload_error(idx, str(exc), name=name))

    commit_session(db)
    if created:
        _bump_product_cache_version()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "products": created,
        "errors": errors,
        "ai_used": use_ai and bool(ai_service.HF_API_TOKEN),
    }


# â”€â”€ Business Profile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CURRENT_TERMS_VERSION = "1.0"

_ALLOWED_PROFILE_FIELDS = {
    "business_name", "business_type", "country", "region", "city",
    "address", "postal_code", "phone_business", "website", "tax_id", "bio",
    # Customer-facing page fields
    "about_us", "logo_url", "banner_url", "video_url",
    "certifications", "social_links", "established_year",
}
_VALID_BUSINESS_TYPES = {"retailer", "wholesaler", "manufacturer", "distributor", "service_provider", "individual"}


def _serialize_supplier_profile(profile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "business_name": profile.business_name,
        "business_type": profile.business_type or "individual",
        "country": profile.country_code,
        "region": profile.region,
        "city": profile.city,
        "address": profile.address,
        "postal_code": profile.postal_code,
        "phone_business": profile.phone_business,
        "website": profile.website,
        "tax_id": profile.tax_id,
        # Customer-facing page fields
        "about_us": getattr(profile, "about_us", None),
        "logo_url": getattr(profile, "logo_url", None),
        "banner_url": getattr(profile, "banner_url", None),
        "video_url": getattr(profile, "video_url", None),
        "certifications": _deserialize_profile_json(getattr(profile, "certifications", None), []),
        "social_links": _deserialize_profile_json(getattr(profile, "social_links", None), {}),
        "established_year": getattr(profile, "established_year", None),
        "bio": profile.bio,
        "is_terms_accepted": bool(profile.is_terms_accepted),
        "terms_version": profile.terms_version,
        "terms_accepted_at": profile.terms_accepted_at.isoformat() if profile.terms_accepted_at else None,
        "verification_status": profile.verification_status or "pending",
        "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
        "created_at": profile.created_at.isoformat(),
    }


def _public_supplier_slug(profile, user: User) -> str:
    preferred_name = getattr(profile, "business_name", None) or getattr(user, "username", None)
    return _slugify_supplier_storefront(preferred_name) or _slugify_supplier_storefront(getattr(user, "username", None))


def get_supplier_profile_business(current_user: dict, db: Session) -> dict:
    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")
    return _serialize_supplier_profile(profile)


def update_supplier_profile_business(body: dict, current_user: dict, db: Session) -> dict:
    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")
    for field in _ALLOWED_PROFILE_FIELDS:
        if field not in body:
            continue
        value = body[field]
        if field == "business_type" and value not in _VALID_BUSINESS_TYPES:
            continue
        if field in _PROFILE_JSON_ARRAY_FIELDS:
            value = _serialize_profile_json(value, "array")
        elif field in _PROFILE_JSON_OBJECT_FIELDS:
            value = _serialize_profile_json(value, "object")
        elif field == "established_year":
            if value in (None, ""):
                value = None
            else:
                try:
                    value = int(value)
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=400, detail="Established year must be a number") from exc
        else:
            value = _sanitize_profile_string(value)
        if field == "website" and isinstance(value, str) and value and not value.startswith(("http://", "https://")):
            value = "https://" + value
        setattr(profile, "country_code" if field == "country" else field, value)
    commit_and_refresh(db, profile)
    bump_cache_version("public_suppliers")
    return _serialize_supplier_profile(profile)


def upload_supplier_profile_business_media(
    field: str,
    file: UploadFile,
    current_user: dict,
    db: Session,
    index: Optional[int] = None,
) -> dict:
    from models import SupplierProfile as SP

    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")

    field_config = _SUPPLIER_PROFILE_MEDIA_FIELDS.get(field)
    if not field_config:
        raise HTTPException(status_code=400, detail="Unsupported supplier storefront media field")

    media_url = _save_supplier_profile_media_upload(file, current_user["id"], field, db=db)

    response_payload: dict[str, Any] = {
        "detail": f"Supplier {field_config['label']} uploaded successfully",
        "field": field,
        "media_url": media_url,
    }

    if field == "certification_image":
        certifications = _deserialize_profile_json(getattr(profile, "certifications", None), [])
        if index is None or index < 0:
            raise HTTPException(status_code=400, detail="Certification index is required")
        if index > len(certifications):
            raise HTTPException(status_code=400, detail="Certification index out of range")

        if index == len(certifications):
            certifications.append({})

        existing_cert = certifications[index] if isinstance(certifications[index], dict) else {}
        updated_cert = {
            **existing_cert,
            "image_url": media_url,
        }
        certifications[index] = _sanitize_profile_json(updated_cert)
        profile.certifications = json.dumps(_sanitize_profile_json(certifications))
        response_payload["index"] = index
    else:
        setattr(profile, field, media_url)

    commit_and_refresh(db, profile)
    response_payload["profile"] = _serialize_supplier_profile(profile)
    return response_payload


def accept_supplier_terms(current_user: dict, db: Session) -> dict:
    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"])
    profile.is_terms_accepted = True
    profile.terms_version = CURRENT_TERMS_VERSION
    profile.terms_accepted_at = utcnow()
    commit_session(db)
    return {"detail": "Terms accepted", "terms_version": CURRENT_TERMS_VERSION}


def get_supplier_onboarding_status(current_user: dict, db: Session) -> dict:
    from models import SupplierProfile as SP
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    products_count = db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).count()
    return {
        "profile_complete": bool(profile and profile.business_name and profile.country_code),
        "terms_accepted": bool(profile and profile.is_terms_accepted),
        "first_product_uploaded": products_count > 0,
        "products_count": products_count,
        "verification_status": profile.verification_status if profile else "pending",
    }


# â”€â”€ Regions / Countries of Operation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_regions(current_user: dict, db: Session) -> dict:
    """Return the supplier's configured operating regions."""
    from models import SupplierProfile as SP
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    raw = (profile.operating_regions if profile else None) or "[]"
    try:
        regions = json.loads(raw)
    except Exception:
        regions = []
    return {
        "operating_regions": regions,
        "origin_country": profile.country_code if profile else None,
        "city": profile.city if profile else None,
    }


def update_supplier_regions(body: dict, current_user: dict, db: Session) -> dict:
    """Save the supplier's list of operating countries/regions."""
    from models import SupplierProfile as SP
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"])
    regions = body.get("operating_regions", [])
    if not isinstance(regions, list):
        raise HTTPException(status_code=422, detail="operating_regions must be a list")
    # sanitize â€” keep plain strings only, max 200 entries
    sanitized = [str(r).strip()[:100] for r in regions if r][:200]
    profile.operating_regions = json.dumps(sanitized)
    if "origin_country" in body and isinstance(body["origin_country"], str):
        profile.country_code = body["origin_country"].strip()[:100] or profile.country_code
    if "city" in body and isinstance(body["city"], str):
        profile.city = body["city"].strip()[:100] or profile.city
    commit_session(db)
    return {"operating_regions": sanitized, "origin_country": profile.country_code, "city": profile.city}


# â”€â”€ Credibility Badge & Document Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_BADGE_THRESHOLDS = {
    # (min_credibility_score, label)
    "gold": 85,
    "silver": 65,
    "bronze": 40,
    "none": 0,
}
_FULFILLED_ORDER_STATUSES = ("completed", "delivered", "shipped")
_MANUAL_BADGE_LEVELS = {"membership", "verified"}
_BADGE_AMOUNT_QUANT = Decimal("0.001")


def _round_badge_amount(value: object) -> Decimal:
    return to_decimal(value).quantize(_BADGE_AMOUNT_QUANT, rounding=ROUND_HALF_UP)


def _ensure_supplier_profile_record(supplier_id: int, db: Session) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
    if not profile:
        profile = SupplierProfile(user_id=supplier_id, verification_status="pending")
        add_and_flush(db, profile)
    return profile


def _start_of_month(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return value.replace(month=value.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_year(value: datetime) -> datetime:
    return value.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _start_of_next_year(value: datetime) -> datetime:
    return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _badge_period_bounds(interval: Optional[str], reference_time: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
    normalized = str(interval or "").strip().lower()
    if normalized == "monthly":
        return _start_of_month(reference_time), _start_of_next_month(reference_time)
    if normalized in {"annual", "yearly"}:
        return _start_of_year(reference_time), _start_of_next_year(reference_time)
    return None, None


def _load_active_badge_tiers(db: Session) -> list[CommissionBadgeTier]:
    rows = (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .all()
    )
    if rows:
        return rows

    from services import commission_engine as _commission_engine

    _commission_engine.seed_defaults(db)
    return (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.is_active == True)  # noqa: E712
        .order_by(CommissionBadgeTier.sort_order.asc(), CommissionBadgeTier.id.asc())
        .all()
    )


def _badge_tier_meets_metrics(tier: CommissionBadgeTier, metrics: dict[str, Any]) -> bool:
    required_orders = int(getattr(tier, "min_fulfilled_orders", None) or 0)
    required_revenue = to_decimal(getattr(tier, "min_monthly_revenue", None) or 0)
    return int(metrics["fulfilled_orders"]) >= required_orders and to_decimal(metrics["monthly_revenue"]) >= required_revenue


def _compute_badge_threshold_metrics(supplier_id: int, db: Session, reference_time: Optional[datetime] = None) -> dict[str, Any]:
    now = reference_time or utcnow()
    month_start = _start_of_month(now)

    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
        )
        .scalar()
    ) or 0

    monthly_revenue = (
        db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
        .select_from(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(_FULFILLED_ORDER_STATUSES),
            Order.created_at >= month_start,
        )
        .scalar()
    ) or 0

    return {
        "fulfilled_orders": int(fulfilled_orders),
        "monthly_revenue": _round_badge_amount(monthly_revenue),
        "month_start": month_start,
        "month_label": month_start.strftime("%Y-%m"),
    }


def _select_eligible_badge_tier(metrics: dict[str, Any], db: Session) -> Optional[CommissionBadgeTier]:
    tiers = _load_active_badge_tiers(db)
    fallback = next((tier for tier in tiers if str(tier.badge_level or "").lower() == "none"), None)
    selected = fallback
    for tier in tiers:
        level = str(tier.badge_level or "").lower()
        if level in _MANUAL_BADGE_LEVELS:
            continue
        if level == "none":
            continue
        if _badge_tier_meets_metrics(tier, metrics):
            selected = tier
    return selected


def _serialize_badge_billing_record(record: BadgeBillingRecord) -> dict[str, Any]:
    supplier = getattr(record, "supplier", None)
    txn = getattr(record, "bank_transaction", None)
    return {
        "id": record.id,
        "billing_reference": record.billing_reference,
        "supplier_id": record.supplier_id,
        "supplier_name": getattr(supplier, "username", None),
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "charge_source": record.charge_source,
        "status": record.status,
        "amount": float(_round_badge_amount(record.amount)),
        "currency": record.currency,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "due_at": record.due_at,
        "billed_at": record.billed_at,
        "paid_at": record.paid_at,
        "payment_method": record.payment_method,
        "bank_transaction_id": record.bank_transaction_id,
        "transaction_ref": getattr(txn, "transaction_ref", None),
        "notes": record.notes,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _find_existing_badge_billing(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    db: Session,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> Optional[BadgeBillingRecord]:
    q = db.query(BadgeBillingRecord).filter(
        BadgeBillingRecord.supplier_id == supplier_id,
        BadgeBillingRecord.badge_level == badge_level,
        BadgeBillingRecord.charge_type == charge_type,
        BadgeBillingRecord.status.in_(("draft", "invoiced", "paid")),
    )
    if charge_type == "setup":
        return q.order_by(BadgeBillingRecord.created_at.desc()).first()
    if period_start is not None:
        q = q.filter(BadgeBillingRecord.period_start == period_start)
    if period_end is not None:
        q = q.filter(BadgeBillingRecord.period_end == period_end)
    return q.order_by(BadgeBillingRecord.created_at.desc()).first()


def _create_badge_billing_record(
    supplier_id: int,
    badge_level: str,
    charge_type: str,
    amount: Decimal,
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
    notes: Optional[str] = None,
    payment_method: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    due_at: Optional[datetime] = None,
) -> tuple[BadgeBillingRecord, bool]:
    existing = _find_existing_badge_billing(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        db=db,
        period_start=period_start,
        period_end=period_end,
    )
    if existing:
        return existing, False

    now = utcnow()
    normalized_amount = _round_badge_amount(amount)
    status = "paid" if normalized_amount <= 0 else "invoiced"
    record = BadgeBillingRecord(
        billing_reference=f"BDG-{uuid.uuid4().hex[:10].upper()}",
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        charge_source=charge_source,
        status=status,
        amount=normalized_amount,
        currency=settings.default_currency,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
        billed_at=now,
        paid_at=now if status == "paid" else None,
        payment_method=payment_method,
        notes=notes,
        created_by=created_by,
    )
    add_and_flush(db, record)
    return record, True


def _maybe_create_recurring_badge_billing(
    supplier_id: int,
    badge_level: str,
    badge_granted_at: Optional[datetime],
    db: Session,
    *,
    charge_source: str,
    created_by: Optional[int],
) -> Optional[BadgeBillingRecord]:
    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        return None

    recurring_fee = _round_badge_amount(getattr(tier, "recurring_fee", 0) or 0)
    if recurring_fee <= 0:
        return None

    period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
    if period_start is None or period_end is None:
        return None

    if badge_granted_at and badge_granted_at >= period_start:
        return None

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type="recurring",
        amount=recurring_fee,
        db=db,
        charge_source=charge_source,
        created_by=created_by,
        notes=f"Recurring {badge_level} badge fee for {period_start.strftime('%Y-%m')}",
        period_start=period_start,
        period_end=period_end,
        due_at=period_end,
    )
    return record if created else None


def list_supplier_badge_catalog(current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    profile = _ensure_supplier_profile_record(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    current_badge = str(profile.badge_level or "none").lower()

    tiers = []
    for tier in _load_active_badge_tiers(db):
        badge_level = str(tier.badge_level or "none").lower()
        tiers.append({
            "badge_level": badge_level,
            "commission_rate": float(tier.commission_rate),
            "setup_fee": float(_round_badge_amount(tier.setup_fee)),
            "recurring_fee": float(_round_badge_amount(tier.recurring_fee)),
            "recurring_interval": tier.recurring_interval,
            "min_fulfilled_orders": tier.min_fulfilled_orders,
            "min_monthly_revenue": float(_round_badge_amount(tier.min_monthly_revenue or 0)),
            "is_active": bool(tier.is_active),
            "is_current": badge_level == current_badge,
            "is_eligible": _badge_tier_meets_metrics(tier, metrics) if badge_level not in _MANUAL_BADGE_LEVELS else False,
            "is_recommended": badge_level == str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        })

    return {
        "supplier_id": supplier_id,
        "current_badge_level": current_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "tiers": tiers,
    }


def list_supplier_badge_billing_history(current_user: dict, db: Session) -> list[dict[str, Any]]:
    supplier_id = int(current_user["id"])
    rows = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.supplier_id == supplier_id)
        .order_by(BadgeBillingRecord.created_at.desc())
        .limit(100)
        .all()
    )
    return [_serialize_badge_billing_record(row) for row in rows]


def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_user: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    record = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.id == billing_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Badge billing record not found")
    if record.status == "paid":
        return _serialize_badge_billing_record(record)
    if record.status in {"waived", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"Cannot record payment for {record.status} badge billing")

    paid_at = utcnow()
    if _round_badge_amount(record.amount) > 0 and not record.bank_transaction_id:
        from services.cash_management_service import log_bank_transaction

        txn = log_bank_transaction(
            source="badge_billing",
            transaction_type="inflow",
            category="badge_fee",
            amount=_round_badge_amount(record.amount),
            db=db,
            currency=record.currency,
            supplier_id=record.supplier_id,
            description=f"{record.charge_type.title()} badge fee collected for {record.badge_level} tier",
            transaction_ref=transaction_ref,
            transaction_date=paid_at,
        )
        record.bank_transaction_id = txn.id
        record.bank_transaction = txn

    record.status = "paid"
    record.payment_method = payment_method.strip().lower() or "manual"
    record.paid_at = paid_at
    if notes:
        record.notes = notes if not record.notes else f"{record.notes}\n{notes}"

    flush_session(db)
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_billing",
        resource_id=record.id,
        details={"status": record.status, "payment_method": record.payment_method, "badge_level": record.badge_level},
    )
    commit_and_refresh(db, record)
    return _serialize_badge_billing_record(record)


def purchase_supplier_badge(body: dict, current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = int(current_user["id"])
    badge_level = str(body.get("badge_level") or "").strip().lower()
    notes = str(body.get("notes") or "").strip() or None
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required")
    if not badge_level or badge_level in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        raise HTTPException(status_code=422, detail="Select a purchasable badge tier")

    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.badge_level == badge_level,
            CommissionBadgeTier.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not tier:
        raise HTTPException(status_code=404, detail="Badge tier not found")

    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    if not _badge_tier_meets_metrics(tier, metrics):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Supplier is not yet eligible for {badge_level}. "
                f"Requires {int(getattr(tier, 'min_fulfilled_orders', None) or 0)} fulfilled orders and "
                f"{float(_round_badge_amount(getattr(tier, 'min_monthly_revenue', None) or 0))} monthly revenue."
            ),
        )

    profile = _ensure_supplier_profile_record(supplier_id, db)
    previous_badge = str(profile.badge_level or "none").lower()
    charge_type = "recurring" if previous_badge == badge_level else "setup"
    amount = _round_badge_amount(tier.recurring_fee if charge_type == "recurring" else tier.setup_fee)
    period_start, period_end = (None, None)
    due_at = utcnow() + timedelta(days=7)

    if charge_type == "recurring":
        period_start, period_end = _badge_period_bounds(getattr(tier, "recurring_interval", None), utcnow())
        if period_start is None or period_end is None:
            raise HTTPException(status_code=422, detail="This badge tier does not have a recurring billing interval")
        due_at = period_end

    record, created = _create_badge_billing_record(
        supplier_id=supplier_id,
        badge_level=badge_level,
        charge_type=charge_type,
        amount=amount,
        db=db,
        charge_source="manual_purchase",
        created_by=supplier_id,
        notes=notes,
        payment_method="manual" if amount <= 0 else None,
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
    )

    if charge_type == "setup" and previous_badge != badge_level:
        profile.badge_level = badge_level
        profile.badge_granted_at = utcnow()

    profile.credibility_score = compute_credibility_score(supplier_id, db)
    flush_session(db)

    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=supplier_id,
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="badge_purchase",
        resource_id=record.id,
        details={
            "badge_level": badge_level,
            "charge_type": charge_type,
            "amount": float(_round_badge_amount(record.amount)),
            "created": created,
        },
    )

    commit_and_refresh(db, record)
    return {
        "badge_level": str(profile.badge_level or "none").lower(),
        "billing": _serialize_badge_billing_record(record),
        "created": created,
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
    }


def compute_credibility_score(supplier_id: int, db: Session) -> int:
    """
    Compute a 0-100 credibility score based on:
      - Order fulfilment rate        (max 35 pts)
      - Average product review score (max 25 pts)
      - Document verification status (max 20 pts)
      - Account age in days          (max 10 pts)
      - Number of approved products  (max 10 pts)
    """
    from models import SupplierProfile as SP, Product, Order, OrderItem, Review

    # 1. Fulfilment rate
    total_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    fulfilled_orders = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem)
        .join(Product)
        .filter(
            Product.supplier_id == supplier_id,
            Order.status.in_(["completed", "delivered", "shipped"]),
        )
        .scalar()
    ) or 0
    fulfilment_rate = (fulfilled_orders / total_orders) if total_orders > 0 else 0
    pts_fulfilment = round(fulfilment_rate * 35)

    # 2. Average review
    avg_review = (
        db.query(func.avg(Review.rating))
        .join(Product, Review.product_id == Product.id)
        .filter(Product.supplier_id == supplier_id)
        .scalar()
    ) or 0
    pts_review = round((float(avg_review) / 5.0) * 25)

    # 3. Document verification
    profile = db.query(SP).filter(SP.user_id == supplier_id).first()
    docs = {}
    if profile and profile.verified_documents:
        try:
            docs = json.loads(profile.verified_documents)
        except Exception:
            docs = {}
    pts_docs = 0
    if profile and profile.verification_status in ("approved", "verified"):
        pts_docs = 20
    elif docs:
        pts_docs = min(15, len(docs) * 5)

    # 4. Account age
    user = db.query(User).filter(User.id == supplier_id).first()
    age_days = 0
    if user and user.created_at:
        age_days = max(0, (utcnow() - user.created_at).days)
    pts_age = min(10, age_days // 30)  # 1pt per month, max 10

    # 5. Approved products
    approved_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.supplier_id == supplier_id,
            Product.is_approved == True,  # noqa: E712
            Product.is_deleted == False,  # noqa: E712
        )
        .scalar()
    ) or 0
    pts_products = min(10, approved_count)

    return int(pts_fulfilment + pts_review + pts_docs + pts_age + pts_products)


def _badge_for_score(score: int) -> str:
    if score >= _BADGE_THRESHOLDS["gold"]:
        return "gold"
    if score >= _BADGE_THRESHOLDS["silver"]:
        return "silver"
    if score >= _BADGE_THRESHOLDS["bronze"]:
        return "bronze"
    return "none"


def refresh_supplier_badge(supplier_id: int, db: Session) -> dict:
    """Recompute credibility score and align badge assignment to tier thresholds."""
    profile = _ensure_supplier_profile_record(supplier_id, db)
    score = compute_credibility_score(supplier_id, db)
    metrics = _compute_badge_threshold_metrics(supplier_id, db)
    eligible_tier = _select_eligible_badge_tier(metrics, db)
    previous_badge = str(profile.badge_level or "none").lower()

    if previous_badge in _MANUAL_BADGE_LEVELS:
        resolved_badge = previous_badge
    else:
        resolved_badge = str(getattr(eligible_tier, "badge_level", None) or _badge_for_score(score)).lower()

    profile.credibility_score = score
    created_billings: list[dict[str, Any]] = []
    if previous_badge != resolved_badge:
        profile.badge_level = resolved_badge
        profile.badge_granted_at = utcnow()
        if eligible_tier is not None and resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
            record, created = _create_badge_billing_record(
                supplier_id=supplier_id,
                badge_level=resolved_badge,
                charge_type="setup",
                amount=_round_badge_amount(getattr(eligible_tier, "setup_fee", 0) or 0),
                db=db,
                charge_source="automatic_recalculation",
                created_by=None,
                notes=f"Automatic badge recalculation promoted supplier to {resolved_badge}",
                due_at=utcnow() + timedelta(days=7),
            )
            if created:
                created_billings.append(_serialize_badge_billing_record(record))
        audit_log(
            db=db,
            action=AuditAction.PROFILE_UPDATED,
            user_id=None,
            username="system",
            user_role="system",
            resource_type="supplier_badge",
            resource_id=supplier_id,
            details={"previous_badge": previous_badge, "badge_level": resolved_badge, "source": "automatic_recalculation"},
        )

    recurring_billing = None
    if resolved_badge not in {"none", *sorted(_MANUAL_BADGE_LEVELS)}:
        recurring_record = _maybe_create_recurring_badge_billing(
            supplier_id=supplier_id,
            badge_level=resolved_badge,
            badge_granted_at=profile.badge_granted_at,
            db=db,
            charge_source="scheduled_recurring",
            created_by=None,
        )
        if recurring_record is not None:
            recurring_billing = _serialize_badge_billing_record(recurring_record)

    commit_session(db)
    bump_cache_version("public_suppliers")
    return {
        "supplier_id": supplier_id,
        "credibility_score": score,
        "badge_level": str(profile.badge_level or "none").lower(),
        "previous_badge_level": previous_badge,
        "eligible_badge_level": str(getattr(eligible_tier, "badge_level", "none") or "none").lower(),
        "fulfilled_orders": metrics["fulfilled_orders"],
        "monthly_revenue": float(metrics["monthly_revenue"]),
        "month_label": metrics["month_label"],
        "billing_records_created": created_billings,
        "recurring_billing": recurring_billing,
    }


def run_badge_recalculation_cycle(db: Session) -> dict[str, Any]:
    supplier_ids = [supplier_id for supplier_id, in db.query(User.id).filter(User.role == "supplier").all()]
    changed = 0
    invoiced = 0
    recurring = 0
    snapshots: list[dict[str, Any]] = []
    for supplier_id in supplier_ids:
        snapshot = refresh_supplier_badge(int(supplier_id), db)
        snapshots.append(snapshot)
        if snapshot.get("previous_badge_level") != snapshot.get("badge_level"):
            changed += 1
        invoiced += len(snapshot.get("billing_records_created") or [])
        recurring += 1 if snapshot.get("recurring_billing") else 0
    return {
        "suppliers_processed": len(supplier_ids),
        "badges_changed": changed,
        "billings_created": invoiced,
        "recurring_billings_created": recurring,
        "snapshots": snapshots,
    }


async def upload_verification_documents(
    files: list,
    doc_types: list[str],
    current_user: dict,
    db: Session,
) -> dict:
    """
    Upload KYC/verification documents for the supplier.
    Stores file paths in SupplierProfile.verified_documents (JSON).
    """
    from models import SupplierProfile as SP
    from utils.file_validation import validate_upload_image
    from utils.config import settings as _settings

    _VALID_DOC_TYPES = {"trade_license", "tax_certificate", "id_front", "id_back", "bank_statement", "other"}

    profile = db.query(SP).filter(SP.user_id == current_user["id"]).first()
    if not profile:
        profile = create_supplier_profile(db, user_id=current_user["id"], verification_status="pending")

    existing_docs = {}
    if profile.verified_documents:
        try:
            existing_docs = json.loads(profile.verified_documents)
        except Exception:
            existing_docs = {}

    from services.storage import storage as _storage

    saved = {}
    for file, doc_type in zip(files, doc_types):
        if doc_type not in _VALID_DOC_TYPES:
            continue
        content = await file.read()
        try:
            ext = validate_upload_image(content, file.filename or "doc")
        except Exception:
            fname_lower = (file.filename or "").lower()
            if not fname_lower.endswith(".pdf"):
                continue
            ext = ".pdf"
        filename = f"doc_{current_user['id']}_{doc_type}_{uuid.uuid4().hex[:6]}{ext}"
        key = f"supplier_documents/{filename}"
        mime_type = file.content_type or "application/octet-stream"
        saved[doc_type] = _storage.save(key, content, content_type=mime_type)

    existing_docs.update(saved)
    profile.verified_documents = json.dumps(existing_docs)
    profile.document_expires_at = None  # admin sets expiry after review
    commit_session(db)

    # auto-refresh badge score after upload
    refresh_supplier_badge(current_user["id"], db)

    return {
        "uploaded": list(saved.keys()),
        "all_documents": existing_docs,
    }


_PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}


def get_supplier_analytics_timeseries(
    current_user: dict,
    period: str,
    db: Session,
) -> dict:
    """Return daily revenue and order counts for the authenticated supplier."""
    supplier_id = current_user["id"]
    if current_user["role"] not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")

    days = _PERIOD_DAYS.get(period, 30)
    since = utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.count(Order.id.distinct()).label("orders"),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Product.supplier_id == supplier_id,
            Order.created_at >= since,
            Order.status != "cancelled",
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )

    return {
        "period": period,
        "data": [
            {"date": str(r.day), "orders": r.orders, "revenue": float(r.revenue)}
            for r in rows
        ],
    }


def admin_set_supplier_badge(
    supplier_user_id: int,
    badge_level: str,
    current_user: dict,
    db: Session,
) -> dict:
    """Admin: manually override badge level for a supplier."""
    from models import SupplierProfile as SP
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    normalized_badge_level = str(badge_level or "").strip().lower()
    valid_badges = {"none", "bronze", "silver", "gold", "membership", "verified"}
    if normalized_badge_level not in valid_badges:
        raise HTTPException(status_code=422, detail=f"badge_level must be one of: {', '.join(sorted(valid_badges))}")
    profile = db.query(SP).filter(SP.user_id == supplier_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    profile.badge_level = normalized_badge_level
    profile.badge_granted_at = utcnow()
    commit_session(db)
    bump_cache_version("public_suppliers")
    audit_log(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        user_id=current_user["id"],
        username=current_user["username"],
        user_role=current_user["role"],
        resource_type="supplier_badge",
        resource_id=supplier_user_id,
        details={"badge_level": normalized_badge_level},
    )
    return {
        "supplier_id": supplier_user_id,
        "badge_level": profile.badge_level,
        "badge_granted_at": profile.badge_granted_at.isoformat(),
    }


# â”€â”€ Public (Customer-Facing) Supplier Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _public_storefront_visibility_clause(profile_model, user_model=None):
    visibility_clauses = [
        profile_model.verification_status.in_(["approved", "verified"]),
    ]
    if user_model is not None:
        visibility_clauses.append(user_model.is_verified == True)  # noqa: E712
    return or_(*visibility_clauses)


def _get_public_supplier_aggregates(supplier_ids: list[int], db: Session) -> dict[int, dict[str, float | int]]:
    if not supplier_ids:
        return {}

    from models import Review as ReviewModel

    aggregates: dict[int, dict[str, float | int]] = {
        supplier_id: {
            "product_count": 0,
            "avg_rating": 0.0,
            "total_reviews": 0,
            "total_sales": 0,
        }
        for supplier_id in supplier_ids
    }

    product_rows = (
        db.query(
            Product.supplier_id,
            func.count(Product.id),
            func.avg(Product.rating),
            func.sum(Product.sales_count),
        )
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,  # noqa: E712
        )
        .group_by(Product.supplier_id)
        .all()
    )

    for supplier_id, product_count, avg_rating, total_sales in product_rows:
        aggregates[int(supplier_id)] = {
            **aggregates.get(int(supplier_id), {}),
            "product_count": int(product_count or 0),
            "avg_rating": float(avg_rating or 0.0),
            "total_sales": int(total_sales or 0),
        }

    review_rows = (
        db.query(Product.supplier_id, func.count(ReviewModel.id))
        .join(Product, ReviewModel.product_id == Product.id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,  # noqa: E712
            ReviewModel.is_deleted == False,  # noqa: E712
        )
        .group_by(Product.supplier_id)
        .all()
    )

    for supplier_id, total_reviews in review_rows:
        current = aggregates.get(int(supplier_id), {
            "product_count": 0,
            "avg_rating": 0.0,
            "total_reviews": 0,
            "total_sales": 0,
        })
        current["total_reviews"] = int(total_reviews or 0)
        aggregates[int(supplier_id)] = current

    return aggregates


def _normalize_supplier_lookup_token(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _supplier_lookup_sql_expression(column):
    return func.lower(
        func.replace(
            func.replace(
                func.replace(
                    func.replace(func.coalesce(column, ""), " ", ""),
                    "-",
                    "",
                ),
                "_",
                "",
            ),
            ".",
            "",
        )
    )

def _get_public_supplier_record(supplier_id: int, db: Session):
    from models import SupplierProfile as SP

    row = (
        db.query(User, SP)
        .join(SP, SP.user_id == User.id)
        .filter(
            User.id == supplier_id,
            User.is_active == 1,
            User.role == "supplier",
            _public_storefront_visibility_clause(SP, User),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return row

def list_public_suppliers(
    q: Optional[str],
    names: Optional[str],
    country: Optional[str],
    limit: int,
    offset: int,
    db: Session,
) -> dict:
    """
    Return active suppliers for the customer discovery page.
    No PII is exposed â€” only business-facing fields.
    """
    region_code = normalize_country_code(country)
    cache_key = _build_public_supplier_cache_key(
        "list",
        {
            "q": (q or "").strip().lower(),
            "names": names or "",
            "country": region_code,
            "limit": limit,
            "offset": offset,
        },
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    from models import SupplierProfile as SP

    base_query = db.query(SP, User).join(User, User.id == SP.user_id).filter(
        User.is_active == 1,
        User.role == "supplier",
        _public_storefront_visibility_clause(SP, User),
    )

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.filter(
            or_(
                User.username.ilike(term),
                SP.business_name.ilike(term),
                SP.bio.ilike(term),
                SP.city.ilike(term),
                SP.region.ilike(term),
                SP.country_code.ilike(term),
            )
        )

    supplier_names = [value.strip() for value in (names or "").split(",") if value.strip()]
    if supplier_names:
        if len(supplier_names) == 1:
            exact_name = supplier_names[0]
            base_query = base_query.filter(
                or_(
                    User.username.ilike(exact_name),
                    SP.business_name.ilike(exact_name),
                )
            )
        else:
            base_query = base_query.filter(
                or_(
                    User.username.in_(supplier_names),
                    SP.business_name.in_(supplier_names),
                )
            )

    profiles = base_query.order_by(User.created_at.desc(), User.id.desc()).all()

    if region_code:
        profiles = [
            (profile, user)
            for profile, user in profiles
            if not normalize_country_code(getattr(profile, "country_code", None))
            or normalize_country_code(getattr(profile, "country_code", None)) == region_code
        ]

    total = len(profiles)
    profiles = profiles[offset : offset + limit]

    aggregates = _get_public_supplier_aggregates([user.id for profile, user in profiles], db)
    items = [
        _build_public_supplier_summary(profile, user, aggregates.get(user.id, {}))
        for profile, user in profiles
    ]

    payload = {"total": total, "items": items}
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def resolve_public_supplier_slug(slug: str, db: Session) -> dict:
    cache_key = _build_public_supplier_cache_key("slug", {"slug": slug.strip().lower()})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    from models import SupplierProfile as SP

    normalized_slug = _normalize_supplier_lookup_token(slug)
    if not normalized_slug:
        raise HTTPException(status_code=404, detail="Supplier not found")

    base_query = db.query(User, SP).join(SP, SP.user_id == User.id).filter(
        User.is_active == 1,
        User.role == "supplier",
        _public_storefront_visibility_clause(SP, User),
    )

    row = base_query.filter(
        or_(
            _supplier_lookup_sql_expression(User.username) == normalized_slug,
            _supplier_lookup_sql_expression(SP.business_name) == normalized_slug,
        )
    ).first()

    if not row:
        for user, profile in base_query.all():
            if _normalize_supplier_lookup_token(user.username) == normalized_slug:
                row = (user, profile)
                break
            if _normalize_supplier_lookup_token(getattr(profile, "business_name", None)) == normalized_slug:
                row = (user, profile)
                break

    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")

    user, profile = row
    aggregates = _get_public_supplier_aggregates([user.id], db)
    storefront_slug = _public_supplier_slug(profile, user)

    payload = {
        **_build_public_supplier_summary(profile, user, aggregates.get(user.id, {})),
        "canonical_path": f"/supplier={storefront_slug}",
    }
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def get_public_supplier_profile(supplier_id: int, db: Session) -> dict:
    """
    Return the full customer-facing profile for one supplier.
    Sensitive fields (phone, address, tax_id, email) are excluded.
    """
    cache_key = _build_public_supplier_cache_key("profile", {"supplier_id": supplier_id})
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    user, profile = _get_public_supplier_record(supplier_id, db)

    aggregates = _get_public_supplier_aggregates([supplier_id], db).get(
        supplier_id,
        {"product_count": 0, "avg_rating": 0.0, "total_reviews": 0, "total_sales": 0},
    )

    from models import Review as ReviewModel

    recent_reviews = [
        {
            "id": review.id,
            "rating": float(review.rating),
            "comment": review.comment,
            "username": reviewer_name,
            "customer_name": reviewer_name,
            "product_name": product_name,
            "created_at": review.created_at.isoformat(),
            "is_verified_purchase": bool(review.is_verified_purchase),
        }
        for review, product_name, reviewer_name in (
            db.query(ReviewModel, Product.name, User.username)
            .join(Product, ReviewModel.product_id == Product.id)
            .join(User, ReviewModel.user_id == User.id)
            .filter(
                Product.supplier_id == supplier_id,
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,  # noqa: E712
                ReviewModel.is_deleted == False,  # noqa: E712
            )
            .order_by(ReviewModel.created_at.desc())
            .limit(5)
            .all()
        )
    ]

    certifications_raw = getattr(profile, "certifications", None) if profile else None
    certifications: list = []
    if certifications_raw:
        try:
            certifications = json.loads(certifications_raw)
        except Exception:
            certifications = []

    social_links_raw = getattr(profile, "social_links", None) if profile else None
    social_links: dict = {}
    if social_links_raw:
        try:
            social_links = json.loads(social_links_raw)
        except Exception:
            social_links = {}

    payload = {
        "id": user.id,
        "username": user.username,
        "slug": _public_supplier_slug(profile, user),
        "business_name": getattr(profile, "business_name", None) if profile else None,
        "business_type": (getattr(profile, "business_type", None) or "individual") if profile else "individual",
        # Model uses `country_code`; the `country` relationship returns the full config object,
        # so expose the ISO code string for the UI.
        "country": getattr(profile, "country_code", None) if profile else None,
        "country_code": getattr(profile, "country_code", None) if profile else None,
        "region": getattr(profile, "region", None) if profile else None,
        "city": getattr(profile, "city", None) if profile else None,
        "website": getattr(profile, "website", None) if profile else None,
        "bio": getattr(profile, "bio", None) if profile else None,
        "about_us": getattr(profile, "about_us", None) if profile else None,
        "logo_url": getattr(profile, "logo_url", None) if profile else None,
        "banner_url": getattr(profile, "banner_url", None) if profile else None,
        "video_url": getattr(profile, "video_url", None) if profile else None,
        "certifications": certifications,
        "social_links": social_links,
        "established_year": getattr(profile, "established_year", None) if profile else None,
        "verification_status": (getattr(profile, "verification_status", None) or "pending") if profile else "pending",
        "badge_level": (getattr(profile, "badge_level", None) or "none") if profile else "none",
        "credibility_score": (getattr(profile, "credibility_score", None) or 0) if profile else 0,
        "member_since": user.created_at.isoformat(),
        "is_verified": bool(user.is_verified),
        # Aggregated metrics
        "product_count": int(aggregates.get("product_count", 0)),
        "avg_rating": round(float(aggregates.get("avg_rating", 0.0)), 1),
        "total_reviews": int(aggregates.get("total_reviews", 0)),
        "total_sales": int(aggregates.get("total_sales", 0)),
        "recent_reviews": recent_reviews,
    }
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def get_public_supplier_products(
    supplier_id: int, limit: int, offset: int, db: Session
) -> dict:
    """Return paginated active products for the customer-facing supplier page."""
    cache_key = _build_public_supplier_cache_key(
        "products",
        {"supplier_id": supplier_id, "limit": limit, "offset": offset},
    )
    cached_payload = cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    _get_public_supplier_record(supplier_id, db)

    total = db.query(func.count(Product.id)).filter(
        Product.supplier_id == supplier_id,
        Product.is_deleted == False,  # noqa: E712
        Product.is_active == True,  # noqa: E712
    ).scalar() or 0

    products = db.query(Product).filter(
        Product.supplier_id == supplier_id,
        Product.is_deleted == False,  # noqa: E712
        Product.is_active == True,  # noqa: E712
    ).order_by(Product.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": str(p.price),
            "compare_price": str(p.compare_price) if p.compare_price else None,
            "image_url": p.image_url,
            "additional_images": p.images,
            "stock": p.stock,
            "category": p.category,
            "brand": p.brand,
            "rating": p.rating,
            "color": p.color,
            "tags": p.tags,
            "sizes": p.sizes,
            "materials": p.materials,
            "weight": p.weight,
            "dimensions": p.dimensions,
            "is_new": bool(getattr(p, "is_new", False)),
            "is_hot": bool(getattr(p, "is_hot", False)),
            "is_featured": bool(getattr(p, "is_featured", False)),
            "sales_count": p.sales_count,
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]
    payload = {"total": total, "items": items}
    cache_set_json(cache_key, payload, _PUBLIC_SUPPLIER_CACHE_TTL)
    return payload


def _build_public_supplier_summary(profile, user: User, aggregates: dict[str, float | int]) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "slug": _public_supplier_slug(profile, user),
        "business_name": getattr(profile, "business_name", None),
        "country": getattr(profile, "country_code", None),
        "city": getattr(profile, "city", None),
        "logo_url": getattr(profile, "logo_url", None),
        "bio": getattr(profile, "bio", None),
        "badge_level": getattr(profile, "badge_level", None) or "none",
        "verification_status": getattr(profile, "verification_status", None) or "pending",
        "credibility_score": int(aggregates.get("credibility_score", getattr(profile, "credibility_score", 0) or 0)),
        "is_verified": bool(user.is_verified),
        "product_count": int(aggregates.get("product_count", 0)),
        "avg_rating": round(float(aggregates.get("avg_rating", 0.0)), 1),
        "total_reviews": int(aggregates.get("total_reviews", 0)),
        "total_sales": int(aggregates.get("total_sales", 0)),
        "member_since": user.created_at.isoformat(),
    }


# â”€â”€ Supplier Bank Account (Payout Beneficiary) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_supplier_bank_account(current_user: dict, db: Session) -> dict:
    """Return the supplier's own bank account details."""
    supplier_id = int(current_user["id"])
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required.")
    record = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    if record is None:
        return {"configured": False}
    return {
        "configured": True,
        "id": record.id,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": record.account_number,
        "iban": record.iban,
        "swift_code": record.swift_code,
        "routing_number": record.routing_number,
        "currency": record.currency,
        "bank_country": record.bank_country,
        "verification_status": record.verification_status,
        "verification_note": record.verification_note,
        "provider": record.provider,
        "provider_recipient_id": record.provider_recipient_id,
        "provider_status": record.provider_status,
        "provider_last_synced_at": record.provider_last_synced_at.isoformat() if record.provider_last_synced_at else None,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def upsert_supplier_bank_account(body: dict, current_user: dict, db: Session) -> dict:
    """Supplier submits or updates their payout bank account. Triggers re-verification."""
    supplier_id = int(current_user["id"])
    if current_user["role"] != "supplier":
        raise HTTPException(status_code=403, detail="Supplier access required.")

    record = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    is_new = record is None
    updates: dict[str, Any] = {}
    for field in ("beneficiary_name", "bank_name", "branch_name", "account_number",
                  "iban", "swift_code", "routing_number", "currency", "bank_country"):
        value = body.get(field)
        if value is not None:
            updates[field] = value

    # Any update resets verification (only if previously verified/rejected)
    if not is_new and getattr(record, "verification_status", "pending") != "pending":
        updates.update({
            "verification_status": "pending",
            "verification_note": "Resubmitted by supplier â€” awaiting re-verification.",
            "provider": None,
            "provider_recipient_id": None,
            "provider_status": None,
            "provider_last_synced_at": None,
            "verified_at": None,
            "verified_by": None,
        })

    if is_new:
        record = create_supplier_bank_account(db, supplier_id=supplier_id, **updates)
    else:
        record = update_supplier_bank_account(db, record, updates)
    return {
        "ok": True,
        "id": record.id,
        "verification_status": record.verification_status,
        "message": "Bank account saved. Awaiting admin verification." if is_new else "Bank account updated. Awaiting re-verification.",
    }




