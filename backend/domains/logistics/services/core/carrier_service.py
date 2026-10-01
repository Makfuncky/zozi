from __future__ import annotations

"""Carrier service — shipping carrier CRUD operations."""

from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.admin import ShippingCarrier
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _require_supplier(current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    return current_user["id"]


def _serialize_carrier(c: ShippingCarrier) -> dict:
    return {
        "id": c.id,
        "supplier_id": c.supplier_id,
        "name": c.name,
        "code": c.code,
        "tracking_url": c.tracking_url,
        "is_active": c.is_active,
        "notes": c.notes,
        "is_global": c.supplier_id is None,
    }


async def get_carriers(current_user: dict, db: Session) -> list[dict]:
    """Return global platform carriers + this supplier's custom carriers."""
    supplier_id = _require_supplier(current_user)
    carriers = db.query(ShippingCarrier).filter(
        (ShippingCarrier.supplier_id.is_(None)) | (ShippingCarrier.supplier_id == supplier_id),
        ShippingCarrier.is_active.is_(True),
    ).order_by(ShippingCarrier.supplier_id.nullsfirst(), ShippingCarrier.name).limit(100).all()
    return [_serialize_carrier(c) for c in carriers]


async def create_carrier(data: dict, current_user: dict, db: Session) -> dict:
    """Create a supplier-specific custom carrier."""
    supplier_id = _require_supplier(current_user)
    name = str(data.get("name", "")).strip()
    code = str(data.get("code", "")).strip().lower().replace(" ", "_")
    if not name or not code:
        raise HTTPException(status_code=422, detail="name and code are required")
    tracking_url = str(data.get("tracking_url", "")).strip() or None
    if tracking_url and not (tracking_url.startswith("http://") or tracking_url.startswith("https://")):
        raise HTTPException(status_code=422, detail="tracking_url must be an http/https URL")
    carrier = ShippingCarrier(
        supplier_id=supplier_id,
        name=name,
        code=code,
        tracking_url=tracking_url,
        notes=str(data.get("notes", "")).strip() or None,
        is_active=True,
        created_at=_utcnow(),
    )
    db.add(carrier)
    db.commit()
    db.refresh(carrier)
    return _serialize_carrier(carrier)


async def delete_carrier(carrier_id: int, current_user: dict, db: Session) -> dict:
    """Soft-delete (deactivate) a supplier's custom carrier."""
    supplier_id = _require_supplier(current_user)
    carrier = db.query(ShippingCarrier).filter(
        ShippingCarrier.id == carrier_id,
        ShippingCarrier.supplier_id == supplier_id,
    ).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    setattr(carrier, "is_active", False)
    db.commit()
    return {"deleted": True, "id": carrier_id}
