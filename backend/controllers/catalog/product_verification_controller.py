"""
Product Verification Controller — spec checks at supply chain touchpoints.
Supports: supplier_dispatch | logistics_receipt | customer_receipt
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from data.models import ProductVerification, Product, Order, Shipment
from data.services_write_helpers import (
from services.catalog.products_read_service import get_product_by_id
    add_and_flush,
    commit_and_refresh,
    commit_only,
)

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

ALLOWED_TYPES = ("supplier_dispatch", "logistics_receipt", "customer_receipt")
ALLOWED_RESULTS = ("passed", "failed", "partial")


def _serialize(v: ProductVerification) -> dict:
    def _parse(s):
        try:
            return json.loads(s) if s else None
        except (ValueError, TypeError):
            return s

    created_at = cast(Optional[datetime], getattr(v, "created_at", None))

    return {
        "id": v.id,
        "product_id": v.product_id,
        "order_id": v.order_id,
        "shipment_id": v.shipment_id,
        "verified_by": v.verified_by,
        "verification_type": v.verification_type,
        "result": v.result,
        "expected_specs": _parse(v.expected_specs),
        "actual_specs": _parse(v.actual_specs),
        "discrepancies": _parse(v.discrepancies),
        "scan_code": v.scan_code,
        "image_urls": _parse(v.image_urls),
        "notes": v.notes,
        "created_at": created_at.isoformat() if created_at else None,
    }


def list_verifications(
    current_user: dict,
    db: Session,
    product_id: Optional[int] = None,
    order_id: Optional[int] = None,
    verification_type: Optional[str] = None,
    result: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator", "supplier", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    q = _db_productverification_query_0(db)

    if role == "supplier":
        # Only their product verifications
        q = q.join(Product).filter(Product.supplier_id == current_user["id"])
    if product_id:
        q = q.filter(ProductVerification.product_id == product_id)
    if order_id:
        q = q.filter(ProductVerification.order_id == order_id)
    if verification_type:
        q = q.filter(ProductVerification.verification_type == verification_type)
    if result:
        q = q.filter(ProductVerification.result == result)

    total = q.count()
    items = q.order_by(desc(ProductVerification.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [_serialize(v) for v in items],
    }


def create_verification(data: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "supplier", "logistics_partner", "support"):
        raise HTTPException(status_code=403, detail="Access denied")

    v_type = data.get("verification_type")
    if v_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid type. Allowed: {ALLOWED_TYPES}")

    result = data.get("result", "passed")
    if result not in ALLOWED_RESULTS:
        raise HTTPException(status_code=422, detail=f"Invalid result. Allowed: {ALLOWED_RESULTS}")

    product_id = data.get("product_id")
    if not product_id:
        raise HTTPException(status_code=422, detail="product_id is required")

    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Supplier can only verify their own products
    if role == "supplier" and product.supplier_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    def _to_json(val):
        if val is None:
            return None
        return json.dumps(val) if not isinstance(val, str) else val

    verification = ProductVerification(
        product_id=product_id,
        order_id=data.get("order_id"),
        shipment_id=data.get("shipment_id"),
        verified_by=current_user["id"],
        verification_type=v_type,
        result=result,
        expected_specs=_to_json(data.get("expected_specs")),
        actual_specs=_to_json(data.get("actual_specs")),
        discrepancies=_to_json(data.get("discrepancies")),
        scan_code=data.get("scan_code"),
        image_urls=_to_json(data.get("image_urls")),
        notes=data.get("notes"),
    )
    add_and_flush(db, verification)
    commit_and_refresh(db, verification)
    return _serialize(verification)


def update_verification(v_id: int, data: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Access denied")

    verification = _db_productverification_first_1(db, id, v_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if "result" in data:
        result = str(data.get("result") or "").strip().lower()
        if result not in ALLOWED_RESULTS:
            raise HTTPException(status_code=422, detail=f"Invalid result. Allowed: {ALLOWED_RESULTS}")
        verification.result = result
    if "notes" in data:
        verification.notes = data.get("notes")

    commit_and_refresh(db, verification)
    return _serialize(verification)


def bulk_update_verifications(data: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Access denied")

    raw_ids = data.get("verification_ids") or []
    verification_ids = [int(v_id) for v_id in raw_ids]
    if not verification_ids:
        raise HTTPException(status_code=400, detail="No verification IDs provided")

    result = str(data.get("result") or "").strip().lower()
    if result not in ALLOWED_RESULTS:
        raise HTTPException(status_code=422, detail=f"Invalid result. Allowed: {ALLOWED_RESULTS}")

    notes = data.get("notes")
    processed: list[dict] = []
    skipped: list[dict] = []
    for verification_id in list(dict.fromkeys(verification_ids)):
        verification = _db_productverification_first_2(db, id, verification_id)
        if not verification:
            skipped.append({"id": verification_id, "reason": "Verification not found"})
            continue
        verification.result = result
        if notes is not None:
            verification.notes = notes
        processed.append({"id": verification_id, "result": result})

    commit_only(db)
    return {
        "processed": len(processed),
        "skipped": len(skipped),
        "result": result,
        "details": processed,
        "skipped_details": skipped,
    }


def get_verification(v_id: int, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator", "supplier", "logistics_partner", "support"):
        raise HTTPException(status_code=403, detail="Access denied")

    v = _db_productverification_first_3(db, id, v_id)
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    if role == "supplier":
        product = _db_product_first_4(db, id, product_id, v)
        if not product or product.supplier_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    return _serialize(v)

