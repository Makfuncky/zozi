"""Product Verification Service — business logic for supply chain verification."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from data.models import ProductVerification, Product
from services.core.write_helpers import add_and_flush, commit_and_refresh, commit_only


logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)


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

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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