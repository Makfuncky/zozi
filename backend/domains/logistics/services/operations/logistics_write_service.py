"""Logistics write operations: shipping carriers, zones, and shipment events."""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from domains.governance.models.admin import ShippingCarrier, ShippingZone
from domains.governance.ports import get_shipping_carrier_by_id, get_shipping_zone_by_id
from domains.logistics.models.logistics import ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def _is_orm(obj, Model) -> bool:
    """True when ``obj`` is an ORM instance of ``Model`` (vs an id)."""
    return isinstance(obj, Model)


def _apply_changes(record, changes):
    """Apply a dict of field -> value to an ORM row, skipping ``None`` values.

    Mirrors the convention used across the other write services so updates are
    idempotent and never reset fields the caller didn't ask to change.
    """
    for field, value in (changes or {}).items():
        if value is None:
            continue
        if hasattr(record, field):
            setattr(record, field, value)
    return record


def _model_kwargs(Model, kwargs):
    """Keep only kwargs that map to real columns on ``Model`` (absorbs extras)."""
    cols = {c.name for c in Model.__table__.columns}
    return {k: v for k, v in kwargs.items() if k in cols}


def create_shipping_carrier(
    db: Session,
    *,
    name: str,
    code: str,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    is_active: bool = True,
    **extra,
) -> ShippingCarrier:
    """Create a supplier-specific shipping carrier.

    Absorbs caller-supplied extras (e.g. ``tracking_url``/``notes``) that are not
    part of the persisted model so legacy callers keep working.
    """
    carrier = ShippingCarrier(
        **_model_kwargs(
            ShippingCarrier,
            dict(name=name, code=code, supplier_id=supplier_id,
                 country_code=country_code, is_active=is_active, **extra),
        )
    )
    db.add(carrier)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(carrier)
    return carrier


def create_shipping_zone(
    db: Session,
    *,
    name: str,
    countries,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    is_active: bool = True,
    **extra,
) -> ShippingZone:
    """Create a shipping zone. ``countries`` may be a JSON string or list."""
    if isinstance(countries, (list, tuple, dict)):
        countries = json.dumps(countries)
    zone = ShippingZone(
        **_model_kwargs(
            ShippingZone,
            dict(name=name, countries=countries, supplier_id=supplier_id,
                 country_code=country_code, is_active=is_active, **extra),
        )
    )
    db.add(zone)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(zone)
    return zone


def update_shipping_zone(db: Session, zone_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipping zone (id or ORM object)."""
    if _is_orm(zone_or_id, ShippingZone):
        record = zone_or_id
    else:
        record = get_shipping_zone_by_id(db, int(zone_or_id))
        if record is None:
            raise ValueError(f"ShippingZone {zone_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def update_shipping_carrier(db: Session, carrier_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipping carrier.

    Compatible with both the spec form ``(db, id, **changes)`` and the legacy
    controller form ``(db, carrier_obj, {"is_active": False})``.
    """
    if _is_orm(carrier_or_id, ShippingCarrier):
        record = carrier_or_id
    else:
        record = get_shipping_carrier_by_id(db, int(carrier_or_id))
        if record is None:
            raise ValueError(f"ShippingCarrier {carrier_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def update_shipment_event(db: Session, event_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipment event (legacy controller form passes an object + dict)."""
    if _is_orm(event_or_id, ShipmentEvent):
        record = event_or_id
    else:
        record = db.get(ShipmentEvent, int(event_or_id))
        if record is None:
            raise ValueError(f"ShipmentEvent {event_or_id} not found")
    _apply_changes(record, changes or kw)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record


def refresh_model(db: Session, obj) -> None:
    """Refresh an ORM instance from the database (flushes pending changes)."""
    db.refresh(obj)
