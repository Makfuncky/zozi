from __future__ import annotations

"""Zone service — shipping zone management."""

import json
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.admin import ShippingZone
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _require_supplier(current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    return current_user["id"]


def _serialize_zone(z: ShippingZone) -> dict:
    countries_raw = cast(Optional[str], getattr(z, "countries", None))
    created_at = cast(Optional[datetime], getattr(z, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(z, "updated_at", None))
    try:
        countries = json.loads(countries_raw) if countries_raw else []
    except (ValueError, TypeError):
        countries = []
    return {
        "id": z.id,
        "name": z.name,
        "countries": countries,
        "carrier_id": z.carrier_id,
        "carrier_name": z.carrier_name or (z.carrier.name if z.carrier else None),
        "base_price": z.base_price,
        "price_per_kg": z.price_per_kg,
        "free_shipping_above": z.free_shipping_above,
        "estimated_days_min": z.estimated_days_min,
        "estimated_days_max": z.estimated_days_max,
        "is_active": z.is_active,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


async def get_shipping_zones(current_user: dict, db: Session) -> list[dict]:
    supplier_id = _require_supplier(current_user)
    zones = db.query(ShippingZone).filter(
        ShippingZone.supplier_id == supplier_id,
    ).order_by(ShippingZone.name).limit(100).all()
    return [_serialize_zone(z) for z in zones]


async def upsert_shipping_zone(data: dict, current_user: dict, db: Session) -> dict:
    """Create or update a shipping zone."""
    supplier_id = _require_supplier(current_user)
    name = str(data.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")

    countries_raw = data.get("countries", [])
    if not isinstance(countries_raw, list):
        raise HTTPException(status_code=422, detail="countries must be a list of country codes")
    countries = [str(c).strip().upper()[:2] for c in countries_raw if c]

    base_price = float(data.get("base_price", 0))
    price_per_kg = float(data.get("price_per_kg", 0))
    free_above = data.get("free_shipping_above")
    est_min = data.get("estimated_days_min")
    est_max = data.get("estimated_days_max")
    carrier_id_raw = data.get("carrier_id")
    carrier_id = int(carrier_id_raw) if carrier_id_raw not in (None, "") else None
    carrier_name = str(data.get("carrier_name", "")).strip() or None
    free_shipping_above = float(free_above) if free_above is not None else None
    estimated_days_min = int(est_min) if est_min is not None else None
    estimated_days_max = int(est_max) if est_max is not None else None
    is_active = bool(data.get("is_active", True))

    zone_id = data.get("id")
    if zone_id:
        zone = db.query(ShippingZone).filter(
            ShippingZone.id == zone_id,
            ShippingZone.supplier_id == supplier_id,
        ).first()
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        setattr(zone, "name", name)
        setattr(zone, "countries", json.dumps(countries))
        setattr(zone, "carrier_id", carrier_id)
        setattr(zone, "carrier_name", carrier_name)
        setattr(zone, "base_price", base_price)
        setattr(zone, "price_per_kg", price_per_kg)
        setattr(zone, "free_shipping_above", free_shipping_above)
        setattr(zone, "estimated_days_min", estimated_days_min)
        setattr(zone, "estimated_days_max", estimated_days_max)
        setattr(zone, "is_active", is_active)
        setattr(zone, "updated_at", _utcnow())
    else:
        zone = ShippingZone(
            supplier_id=supplier_id,
            name=name,
            countries=json.dumps(countries),
            carrier_id=carrier_id,
            carrier_name=carrier_name,
            base_price=base_price,
            price_per_kg=price_per_kg,
            free_shipping_above=free_shipping_above,
            estimated_days_min=estimated_days_min,
            estimated_days_max=estimated_days_max,
            is_active=True,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        db.add(zone)

    db.commit()
    db.refresh(zone)
    return _serialize_zone(zone)


async def delete_shipping_zone(zone_id: int, current_user: dict, db: Session) -> dict:
    supplier_id = _require_supplier(current_user)
    zone = db.query(ShippingZone).filter(
        ShippingZone.id == zone_id,
        ShippingZone.supplier_id == supplier_id,
    ).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()
    return {"deleted": True, "id": zone_id}
