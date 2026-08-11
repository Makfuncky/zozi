"""Backward-compatible re-export shim for logistics write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.orders.logistics_controller`,
`routers.public_logistics_access` and `routers.public_shipments_access`, which created import-time
circular-import cycles (`logistics_controller` -> `logistics_write_service` ->
`logistics_controller`). Resolving names lazily via module-level `__getattr__`
breaks those cycles: the underlying modules are only imported on first
attribute access, by which point the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "delete_shipping_zone": ("controllers.orders.logistics_controller", "delete_shipping_zone"),
    "update_shipment": ("routers.public_shipments_access", "update_shipment"),
    "add_and_flush": ("services.common.write_helpers", "add_and_flush"),
    "commit_only": ("services.common.write_helpers", "commit_only"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from data.models import ShippingCarrier, ShippingZone, ShipmentEvent
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
            dict(
                name=name,
                code=code,
                supplier_id=supplier_id,
                country_code=country_code,
                is_active=is_active,
                **extra,
            ),
        )
    )
    db.add(carrier)
    db.commit()
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
        import json as _json
        countries = _json.dumps(countries)
    zone = ShippingZone(
        **_model_kwargs(
            ShippingZone,
            dict(
                name=name,
                countries=countries,
                supplier_id=supplier_id,
                country_code=country_code,
                is_active=is_active,
                **extra,
            ),
        )
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def update_shipping_zone(db: Session, zone_or_id, changes: Optional[dict] = None, **kw):
    """Update a shipping zone (id or ORM object)."""
    if _is_orm(zone_or_id, ShippingZone):
        record = zone_or_id
    else:
        record = db.get(ShippingZone, int(zone_or_id))
        if record is None:
            raise ValueError(f"ShippingZone {zone_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
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
        record = db.get(ShippingCarrier, int(carrier_or_id))
        if record is None:
            raise ValueError(f"ShippingCarrier {carrier_or_id} not found")
    _apply_changes(record, changes or kw)
    db.commit()
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
    db.commit()
    db.refresh(record)
    return record


def refresh_model(db: Session, obj) -> None:
    """Refresh an ORM instance from the database (flushes pending changes)."""
    db.refresh(obj)
