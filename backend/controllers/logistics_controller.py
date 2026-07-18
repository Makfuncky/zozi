"""
Logistics controller — shipping carriers, zones, and shipment fulfilment.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from controllers.audit_controller import AuditAction, audit_log
from models import (
    LogisticsPartner,
    Notification,
    Order,
    OrderItem,
    Product,
    ShippingCarrier,
    ShippingZone,
    Shipment,
    ShipmentEvent,
    SupplierProfile,
)
from utils.order_tracking import canonical_scan_code, ensure_shipment_identifiers, reconcile_order_status, shipment_scan_codes
from utils.order_tracking import shipment_event_label, shipment_status_label
from utils.datetime_utils import utcnow as _utcnow
from utils.realtime import logistics_realtime_hub

logger = logging.getLogger(__name__)

SHIPMENT_STATUSES = ("pending", "processing", "picking_up", "shipped", "in_transit", "delivered", "failed", "returned")
EVENT_TO_STATUS = {
    "picked_from_supplier": "shipped",
    "pickup_confirmed": "picking_up",
    "pickup_cancelled": "processing",
    "logistics_received": "shipped",
    "distribution_checkpoint": "in_transit",
    "out_for_delivery": "in_transit",
    "customer_received": "delivered",
    "shipment_failed": "failed",
    "shipment_returned": "returned",
    "shipment_delayed": "in_transit",
    "shipment_rescheduled": "in_transit",
    "shipment_cancelled": "failed",
}


def _parse_optional_positive_int(value: Any) -> Optional[int]:
    if value in (None, "", b""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="package_count must be an integer") from exc
    if parsed <= 0:
        raise HTTPException(status_code=422, detail="package_count must be greater than 0")
    return parsed


def _parse_optional_nonnegative_float(value: Any, field_name: str) -> Optional[float]:
    if value in (None, "", b""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be a number") from exc
    if parsed < 0:
        raise HTTPException(status_code=422, detail=f"{field_name} must be non-negative")
    return parsed


def _parse_optional_datetime(value: Any, field_name: str) -> Optional[datetime]:
    if value in (None, "", b""):
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be a valid ISO datetime") from exc


def _apply_package_metadata(shipment: Shipment, data: dict[str, Any], actor_user_id: Any) -> None:
    touched = False
    if "package_count" in data:
        setattr(shipment, "package_count", _parse_optional_positive_int(data.get("package_count")))
        touched = True
    if "package_weight_kg" in data:
        setattr(
            shipment,
            "package_weight_kg",
            _parse_optional_nonnegative_float(data.get("package_weight_kg"), "package_weight_kg"),
        )
        touched = True
    if "package_dimensions" in data:
        setattr(shipment, "package_dimensions", str(data.get("package_dimensions", "")).strip() or None)
        touched = True
    if "packaged_at" in data:
        setattr(shipment, "packaged_at", _parse_optional_datetime(data.get("packaged_at"), "packaged_at"))
        touched = True
    if "packaging_notes" in data:
        setattr(shipment, "packaging_notes", str(data.get("packaging_notes", "")).strip() or None)
        touched = True

    if touched and actor_user_id is not None:
        setattr(shipment, "packaged_by_user_id", int(actor_user_id))
    if touched and cast(Optional[datetime], getattr(shipment, "packaged_at", None)) is None:
        setattr(shipment, "packaged_at", _utcnow())


# ── helpers ───────────────────────────────────────────────────────────────────

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


def _serialize_shipment(s: Shipment) -> dict:
    order = s.order
    tracking_number = cast(Optional[str], getattr(s, "tracking_number", None))
    shipped_at = cast(Optional[datetime], getattr(s, "shipped_at", None))
    estimated_delivery = cast(Optional[datetime], getattr(s, "estimated_delivery", None))
    actual_delivery = cast(Optional[datetime], getattr(s, "actual_delivery", None))
    packaged_at = cast(Optional[datetime], getattr(s, "packaged_at", None))
    created_at = cast(Optional[datetime], getattr(s, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(s, "updated_at", None))
    carrier_tracking_url = cast(Optional[str], getattr(s.carrier, "tracking_url", None)) if s.carrier else None
    tracking_url = None
    if tracking_number and carrier_tracking_url:
        tracking_url = carrier_tracking_url.replace("{number}", tracking_number)
    status = cast(str, getattr(s, "status", "pending"))
    return {
        "id": s.id,
        "order_id": s.order_id,
        "order_total": order.total_amount if order else None,
        "order_status": order.status if order else None,
        "customer_id": order.user_id if order else None,
        "shipping_address": order.shipping_address if order else None,
        "assigned_partner_id": s.assigned_partner_id,
        "assigned_partner_name": s.assigned_partner.name if s.assigned_partner else None,
        "assigned_partner_code": s.assigned_partner.code if s.assigned_partner else None,
        "carrier_id": s.carrier_id,
        "carrier_name": s.carrier_name or (s.carrier.name if s.carrier else None),
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "status": status,
        "status_label": shipment_status_label(status, shipment=s),
        "distribution_channel": s.distribution_channel,
        "current_hub": s.current_hub,
        "scan_code": s.scan_code,
        "package_count": s.package_count,
        "package_weight_kg": s.package_weight_kg,
        "package_dimensions": s.package_dimensions,
        "packaged_at": packaged_at.isoformat() if packaged_at else None,
        "packaged_by_user_id": s.packaged_by_user_id,
        "packaging_notes": s.packaging_notes,
        "shipped_at": shipped_at.isoformat() if shipped_at else None,
        "estimated_delivery": estimated_delivery.isoformat() if estimated_delivery else None,
        "actual_delivery": actual_delivery.isoformat() if actual_delivery else None,
        "notes": s.notes,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def _publish_supplier_shipment_update(
    shipment: Shipment,
    *,
    event_type: str,
    broadcast_all_partners: bool = False,
) -> None:
    logistics_realtime_hub.publish(
        order_id=cast(int, getattr(shipment, "order_id")),
        payload={
            "type": event_type,
            "shipment_id": cast(int, getattr(shipment, "id")),
            "order_id": cast(int, getattr(shipment, "order_id")),
            "assigned_partner_id": cast(Optional[int], getattr(shipment, "assigned_partner_id", None)),
            "status": cast(str, getattr(shipment, "status", "pending")),
            "tracking_number": cast(Optional[str], getattr(shipment, "tracking_number", None)),
            "current_hub": cast(Optional[str], getattr(shipment, "current_hub", None)),
            "scan_code": canonical_scan_code(shipment),
        },
        broadcast_all_partners=broadcast_all_partners,
    )


def _allowed_scan_codes(shipment: Shipment) -> set[str]:
    return shipment_scan_codes(shipment)


def _serialize_event(event: ShipmentEvent) -> dict:
    created_at = cast(Optional[datetime], getattr(event, "created_at", None))
    return {
        "id": event.id,
        "shipment_id": event.shipment_id,
        "order_id": event.order_id,
        "supplier_id": event.supplier_id,
        "actor_user_id": event.actor_user_id,
        "actor_role": event.actor_role,
        "event_type": event.event_type,
        "event_label": shipment_event_label(event),
        "status_after": event.status_after,
        "distribution_channel": event.distribution_channel,
        "location": event.location,
        "latitude": getattr(event, "latitude", None),
        "longitude": getattr(event, "longitude", None),
        "scan_code": event.scan_code,
        "notes": event.notes,
        "created_at": created_at.isoformat() if created_at else None,
    }


async def update_event_gps(
    event_id: int,
    latitude: float,
    longitude: float,
    current_user: dict,
    db: Session,
) -> dict:
    """Attach GPS coordinates to an existing shipment event."""
    role = current_user.get("role", "")
    if role not in ("supplier", "admin", "superadmin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Forbidden")
    event = db.query(ShipmentEvent).filter(ShipmentEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Shipment event not found")
    # Suppliers may only update events on their own shipments
    if role == "supplier":
        supplier_id = _require_supplier(current_user)
        if event.supplier_id != supplier_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    if role == "logistics_partner":
        partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user.get("id")).first()
        if not partner or not event.shipment or event.shipment.assigned_partner_id != partner.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=422, detail="latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="longitude must be between -180 and 180")
    setattr(event, "latitude", latitude)
    setattr(event, "longitude", longitude)
    db.commit()
    db.refresh(event)
    if event.shipment is not None:
        logistics_realtime_hub.publish(
            partner_id=cast(Optional[int], getattr(event.shipment, "assigned_partner_id", None)),
            order_id=cast(int, getattr(event, "order_id")),
            payload={
                "type": "shipment.gps_updated",
                "shipment_id": event.shipment_id,
                "order_id": event.order_id,
                "assigned_partner_id": cast(Optional[int], getattr(event.shipment, "assigned_partner_id", None)),
                "event": _serialize_event(event),
            },
        )
    return _serialize_event(event)


def _create_shipment_event(
    *,
    shipment: Shipment,
    actor_user_id: Optional[int],
    actor_role: str,
    event_type: str,
    status_after: Optional[str],
    distribution_channel: Optional[str],
    location: Optional[str],
    scan_code: Optional[str],
    notes: Optional[str],
) -> ShipmentEvent:
    return ShipmentEvent(
        shipment_id=shipment.id,
        order_id=shipment.order_id,
        supplier_id=shipment.supplier_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        event_type=event_type,
        status_after=status_after,
        distribution_channel=distribution_channel,
        location=location,
        scan_code=scan_code,
        notes=notes,
        created_at=_utcnow(),
    )


def _resolve_assigned_partner(data: dict[str, Any], db: Session) -> LogisticsPartner | None:
    raw_partner_id = data.get("assigned_partner_id")
    if raw_partner_id in (None, "", b""):
        return None
    try:
        partner_id = int(raw_partner_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="assigned_partner_id must be an integer") from exc

    partner = db.query(LogisticsPartner).filter(LogisticsPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Assigned logistics partner not found")
    if cast(str, getattr(partner, "status", "")) != "active":
        raise HTTPException(status_code=422, detail="Assigned logistics partner must be active")
    return partner


# ── carriers ──────────────────────────────────────────────────────────────────

async def get_carriers(current_user: dict, db: Session) -> list[dict]:
    """Return global platform carriers + this supplier's custom carriers."""
    supplier_id = _require_supplier(current_user)
    carriers = db.query(ShippingCarrier).filter(
        (ShippingCarrier.supplier_id.is_(None)) | (ShippingCarrier.supplier_id == supplier_id),
        ShippingCarrier.is_active.is_(True),
    ).order_by(ShippingCarrier.supplier_id.nullsfirst(), ShippingCarrier.name).all()
    return [_serialize_carrier(c) for c in carriers]


async def create_carrier(data: dict, current_user: dict, db: Session) -> dict:
    """Create a supplier-specific custom carrier."""
    supplier_id = _require_supplier(current_user)
    name = str(data.get("name", "")).strip()
    code = str(data.get("code", "")).strip().lower().replace(" ", "_")
    if not name or not code:
        raise HTTPException(status_code=422, detail="name and code are required")
    tracking_url = str(data.get("tracking_url", "")).strip() or None
    # Validate tracking URL if provided
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


# ── shipping zones ─────────────────────────────────────────────────────────────

async def get_shipping_zones(current_user: dict, db: Session) -> list[dict]:
    supplier_id = _require_supplier(current_user)
    zones = db.query(ShippingZone).filter(
        ShippingZone.supplier_id == supplier_id,
    ).order_by(ShippingZone.name).all()
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


# ── orders to fulfil ──────────────────────────────────────────────────────────

async def get_orders_to_fulfil(current_user: dict, db: Session) -> list[dict]:
    """Return orders containing this supplier's products that still need to be shipped."""
    supplier_id = _require_supplier(current_user)

    # Orders that have items belonging to this supplier and are not yet shipped
    already_shipped_order_ids = [
        row[0] for row in db.query(Shipment.order_id).filter(
            Shipment.supplier_id == supplier_id,
            Shipment.status.notin_(["failed", "returned"]),
        ).all()
    ]

    supplier_product_ids = [
        row[0] for row in db.query(Product.id).filter(
            Product.supplier_id == supplier_id,
            Product.is_deleted == False,  # noqa: E712
        ).all()
    ]

    if not supplier_product_ids:
        return []

    order_ids_with_supplier_items = [
        row[0] for row in db.query(OrderItem.order_id).filter(
            OrderItem.product_id.in_(supplier_product_ids),
        ).distinct().all()
    ]

    orders = db.query(Order).filter(
        Order.id.in_(order_ids_with_supplier_items),
        Order.id.notin_(already_shipped_order_ids),
        Order.status.in_(["confirmed", "paid", "processing"]),
    ).order_by(Order.created_at).all()

    result = []
    for order in orders:
        created_at = cast(Optional[datetime], getattr(order, "created_at", None))
        paid_at = cast(Optional[datetime], getattr(order, "paid_at", None))
        # Only include items belonging to this supplier
        items = [
            i for i in order.items
            if i.product_id in supplier_product_ids
        ]
        result.append({
            "order_id": order.id,
            "order_status": order.status,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "created_at": created_at.isoformat() if created_at else None,
            "paid_at": paid_at.isoformat() if paid_at else None,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product.name if i.product else f"Product #{i.product_id}",
                    "quantity": i.quantity,
                    "price": i.price,
                }
                for i in items
            ],
        })
    return result


# ── shipments ─────────────────────────────────────────────────────────────────

async def create_shipment(data: dict, current_user: dict, db: Session) -> dict:
    """Create a shipment record and move the order into the prepared handoff stage."""
    supplier_id = _require_supplier(current_user)

    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Verify the order contains this supplier's products
    supplier_product_ids = {
        row[0] for row in db.query(Product.id).filter(
            Product.supplier_id == supplier_id,
        ).all()
    }
    has_supplier_item = any(i.product_id in supplier_product_ids for i in order.items)
    if not has_supplier_item and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="This order does not contain your products")

    # Prevent duplicate shipments
    existing = db.query(Shipment).filter(
        Shipment.order_id == order_id,
        Shipment.supplier_id == supplier_id,
        Shipment.status.notin_(["failed", "returned"]),
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Shipment already exists for this order (ID: {existing.id}, status: {existing.status})",
        )

    current_hub = str(data.get("current_hub", "")).strip() or None
    if not current_hub:
        supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
        current_hub = next(
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

    shipment = Shipment(
        order_id=order_id,
        supplier_id=supplier_id,
        assigned_partner_id=None,
        carrier_id=None,
        carrier_name=None,
        tracking_number=None,
        status="processing",
        distribution_channel=None,
        current_hub=current_hub,
        estimated_delivery=None,
        notes=str(data.get("notes", "")).strip() or None,
        created_at=_utcnow(),
    )
    _apply_package_metadata(shipment, cast(dict[str, Any], data), current_user.get("id"))
    db.add(shipment)
    db.flush()

    tracking_number, shipment_scan_code = ensure_shipment_identifiers(shipment)

    # Update order tracking_number if provided
    order_tracking_number = cast(Optional[str], getattr(order, "tracking_number", None))
    if tracking_number and not order_tracking_number:
        setattr(order, "tracking_number", tracking_number)
    setattr(order, "status", "processing")

    shipment_status = cast(str, getattr(shipment, "status"))
    shipment_notes = cast(Optional[str], getattr(shipment, "notes", None))

    db.add(
        _create_shipment_event(
            shipment=shipment,
            actor_user_id=current_user.get("id"),
            actor_role=current_user.get("role", "supplier"),
            event_type="packaging_started",
            status_after=shipment_status,
            distribution_channel=None,
            location=current_hub,
            scan_code=shipment_scan_code,
            notes=shipment_notes,
        )
    )

    audit_log(
        db=db,
        action=AuditAction.ORDER_STATUS_CHANGED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="shipment",
        resource_id=cast(int, getattr(shipment, "id")),
        details={
            "event": "shipment_created",
            "order_id": order_id,
            "status": shipment_status,
            "distribution_channel": None,
            "hub": current_hub,
            "assigned_partner_id": shipment.assigned_partner_id,
            "package_count": shipment.package_count,
            "package_weight_kg": shipment.package_weight_kg,
            "tracking_number": tracking_number,
            "scan_code": shipment_scan_code,
        },
        status="success",
    )

    db.commit()
    db.refresh(shipment)
    _publish_supplier_shipment_update(shipment, event_type="shipment.packaging_started")
    logger.info("Shipment created: order %d by supplier %d → tracking %s", order_id, supplier_id, tracking_number)

    # Auto-create invoice for this shipment if one doesn't exist yet (non-blocking)
    try:
        from models import Invoice
        from controllers.invoice_controller import create_invoice_from_order
        has_invoice = db.query(Invoice).filter(
            Invoice.order_id == order_id,
            Invoice.supplier_id == supplier_id,
            Invoice.invoice_type == "sale",
        ).first()
        if not has_invoice:
            create_invoice_from_order(
                data={"order_id": order_id, "shipment_id": shipment.id},
                current_user=current_user,
                db=db,
            )
            logger.info("Auto-invoice created for order %d supplier %d", order_id, supplier_id)
    except Exception as exc:
        logger.warning("Auto-invoice creation failed (non-fatal): %s", exc)

    return _serialize_shipment(shipment)


async def get_active_shipments(current_user: dict, db: Session) -> list[dict]:
    """Return all non-delivered active shipments for this supplier."""
    supplier_id = _require_supplier(current_user)
    shipments = db.query(Shipment).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.status.notin_(["delivered", "returned"]),
    ).order_by(Shipment.shipped_at.desc()).all()
    return [_serialize_shipment(s) for s in shipments]


async def get_shipment_history(current_user: dict, db: Session, page: int = 1, per_page: int = 30) -> dict:
    """Return paginated fulfilment history for this supplier."""
    supplier_id = _require_supplier(current_user)
    q = db.query(Shipment).filter(Shipment.supplier_id == supplier_id).order_by(Shipment.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [_serialize_shipment(s) for s in items],
    }


async def get_shipment_events(shipment_id: int, current_user: dict, db: Session) -> list[dict]:
    supplier_id = _require_supplier(current_user)
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.supplier_id == supplier_id,
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    events = db.query(ShipmentEvent).filter(
        ShipmentEvent.shipment_id == shipment_id
    ).order_by(ShipmentEvent.created_at.asc()).all()
    return [_serialize_event(event) for event in events]


async def scan_shipment_event(shipment_id: int, data: dict, current_user: dict, db: Session) -> dict:
    supplier_id = _require_supplier(current_user)
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.supplier_id == supplier_id,
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    event_type = str(data.get("event_type", "")).strip()
    if not event_type:
        raise HTTPException(status_code=422, detail="event_type is required")
    if event_type not in EVENT_TO_STATUS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported event_type. Allowed: {', '.join(sorted(EVENT_TO_STATUS.keys()))}",
        )

    submitted_scan_code = str(data.get("scan_code", "")).strip()
    allowed_codes = _allowed_scan_codes(shipment)
    if submitted_scan_code and submitted_scan_code not in allowed_codes:
        raise HTTPException(status_code=409, detail="scan_code does not match this shipment")

    existing_scan_code = cast(Optional[str], getattr(shipment, "scan_code", None))
    resolved_scan_code = submitted_scan_code or existing_scan_code or canonical_scan_code(shipment)
    setattr(shipment, "scan_code", resolved_scan_code)

    status_after = str(data.get("status_after", "")).strip() or EVENT_TO_STATUS[event_type]
    if status_after not in SHIPMENT_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status_after. Allowed: {SHIPMENT_STATUSES}")

    existing_distribution_channel = cast(Optional[str], getattr(shipment, "distribution_channel", None))
    existing_hub = cast(Optional[str], getattr(shipment, "current_hub", None))
    distribution_channel = str(data.get("distribution_channel", "")).strip() or existing_distribution_channel
    location = str(data.get("location", "")).strip() or existing_hub
    notes = str(data.get("notes", "")).strip() or None

    setattr(shipment, "distribution_channel", distribution_channel)
    setattr(shipment, "current_hub", location)
    setattr(shipment, "status", status_after)
    setattr(shipment, "updated_at", _utcnow())

    shipped_at = cast(Optional[datetime], getattr(shipment, "shipped_at", None))
    if status_after in {"shipped", "in_transit"} and not shipped_at:
        setattr(shipment, "shipped_at", _utcnow())
    if status_after == "delivered":
        actual_delivery = cast(Optional[datetime], getattr(shipment, "actual_delivery", None))
        setattr(shipment, "actual_delivery", actual_delivery or _utcnow())
    if shipment.order:
        order_shipments = db.query(Shipment).filter(Shipment.order_id == shipment.order_id).all()
        setattr(shipment.order, "status", reconcile_order_status(shipment.order, order_shipments))
        if status_after == "delivered":
            title = "Order Delivered" if shipment.order.status == "delivered" else "Shipment Delivered"
            message = (
                f"Order #{shipment.order_id} has been fully delivered."
                if shipment.order.status == "delivered"
                else f"One shipment for order #{shipment.order_id} has been delivered."
            )
            db.add(
                Notification(
                    user_id=shipment.order.user_id,
                    type="order_update",
                    title=title,
                    message=message,
                    link=f"/orders/{shipment.order_id}",
                )
            )

    event = _create_shipment_event(
        shipment=shipment,
        actor_user_id=current_user.get("id"),
        actor_role=current_user.get("role", "supplier"),
        event_type=event_type,
        status_after=status_after,
        distribution_channel=distribution_channel,
        location=location,
        scan_code=resolved_scan_code,
        notes=notes,
    )
    db.add(event)

    audit_log(
        db=db,
        action="SHIPMENT_SCAN_EVENT",
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="shipment",
        resource_id=cast(int, getattr(shipment, "id")),
        details={
            "event_type": event_type,
            "status_after": status_after,
            "scan_code": resolved_scan_code,
            "distribution_channel": distribution_channel,
            "location": location,
        },
        status="success",
    )

    db.commit()
    db.refresh(shipment)
    db.refresh(event)
    return {
        "shipment": _serialize_shipment(shipment),
        "event": _serialize_event(event),
    }


async def update_shipment_status(shipment_id: int, data: dict, current_user: dict, db: Session) -> dict:
    """Update supplier-controlled shipment packaging metadata."""
    supplier_id = _require_supplier(current_user)
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.supplier_id == supplier_id,
    ).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    previous_status = cast(str, getattr(shipment, "status"))
    new_notes = data.get("notes")
    if new_notes is not None:
        setattr(shipment, "notes", str(new_notes).strip() or None)

    new_hub = data.get("current_hub")
    if new_hub is not None:
        setattr(shipment, "current_hub", str(new_hub).strip() or None)

    _apply_package_metadata(shipment, cast(dict[str, Any], data), current_user.get("id"))

    setattr(shipment, "updated_at", _utcnow())
    tracking_number, shipment_scan_code = ensure_shipment_identifiers(shipment)

    shipment_status = cast(str, getattr(shipment, "status"))
    shipment_distribution_channel = cast(Optional[str], getattr(shipment, "distribution_channel", None))
    shipment_current_hub = cast(Optional[str], getattr(shipment, "current_hub", None))
    shipment_notes = cast(Optional[str], getattr(shipment, "notes", None))

    if new_notes is not None or new_hub is not None or any(key in data for key in ("package_count", "package_weight_kg", "package_dimensions", "packaged_at", "packaging_notes")):
        db.add(
            _create_shipment_event(
                shipment=shipment,
                actor_user_id=current_user.get("id"),
                actor_role=current_user.get("role", "supplier"),
                event_type="status_manual_update",
                status_after=shipment_status,
                distribution_channel=shipment_distribution_channel,
                location=shipment_current_hub,
                scan_code=shipment_scan_code,
                notes=shipment_notes,
            )
        )

    if shipment.order:
        order_shipments = db.query(Shipment).filter(Shipment.order_id == shipment.order_id).all()
        setattr(shipment.order, "status", reconcile_order_status(shipment.order, order_shipments))

    db.commit()
    db.refresh(shipment)
    return _serialize_shipment(shipment)


async def get_logistics_summary(current_user: dict, db: Session) -> dict:
    """Return a quick stats summary for the logistics dashboard."""
    supplier_id = _require_supplier(current_user)

    total_shipments = db.query(Shipment).filter(Shipment.supplier_id == supplier_id).count()
    pending_shipments = db.query(Shipment).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.status == "pending",
    ).count()
    in_transit = db.query(Shipment).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.status.in_(["shipped", "in_transit"]),
    ).count()
    delivered = db.query(Shipment).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.status == "delivered",
    ).count()

    # Orders awaiting fulfilment count
    supplier_product_ids = [
        row[0] for row in db.query(Product.id).filter(
            Product.supplier_id == supplier_id,
            Product.is_deleted == False,  # noqa: E712
        ).all()
    ]
    shipped_order_ids = [
        row[0] for row in db.query(Shipment.order_id).filter(
            Shipment.supplier_id == supplier_id,
            Shipment.status.notin_(["failed", "returned"]),
        ).all()
    ]
    order_ids_with_items = [
        row[0] for row in db.query(OrderItem.order_id).filter(
            OrderItem.product_id.in_(supplier_product_ids),
        ).distinct().all()
    ] if supplier_product_ids else []

    awaiting_count = db.query(Order).filter(
        Order.id.in_(order_ids_with_items),
        Order.id.notin_(shipped_order_ids),
        Order.status.in_(["confirmed", "paid", "processing"]),
    ).count()

    zones_count = db.query(ShippingZone).filter(
        ShippingZone.supplier_id == supplier_id,
        ShippingZone.is_active == True,  # noqa: E712
    ).count()

    channels_raw = db.query(
        Shipment.distribution_channel,
        Shipment.status,
    ).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.distribution_channel.isnot(None),
    ).all()
    channels: dict[str, dict] = {}
    for channel, status in channels_raw:
        key = str(channel).strip()
        if not key:
            continue
        bucket = channels.setdefault(
            key,
            {"channel": key, "total": 0, "delivered": 0, "in_transit": 0, "pending": 0},
        )
        bucket["total"] += 1
        if status == "delivered":
            bucket["delivered"] += 1
        elif status in {"shipped", "in_transit"}:
            bucket["in_transit"] += 1
        else:
            bucket["pending"] += 1

    return {
        "awaiting_fulfilment": awaiting_count,
        "in_transit": in_transit,
        "delivered_total": delivered,
        "total_shipments": total_shipments,
        "pending_shipments": pending_shipments,
        "active_zones": zones_count,
        "distribution_channels": list(channels.values()),
    }


async def get_distribution_channels(current_user: dict, db: Session) -> list[dict]:
    supplier_id = _require_supplier(current_user)
    rows = db.query(
        Shipment.distribution_channel,
        Shipment.status,
    ).filter(
        Shipment.supplier_id == supplier_id,
        Shipment.distribution_channel.isnot(None),
    ).all()

    channels: dict[str, dict] = {}
    for channel, status in rows:
        name = str(channel).strip()
        if not name:
            continue
        bucket = channels.setdefault(
            name,
            {
                "channel": name,
                "total_shipments": 0,
                "in_transit": 0,
                "delivered": 0,
                "returned_or_failed": 0,
            },
        )
        bucket["total_shipments"] += 1
        if status in {"shipped", "in_transit", "processing"}:
            bucket["in_transit"] += 1
        elif status == "delivered":
            bucket["delivered"] += 1
        elif status in {"returned", "failed"}:
            bucket["returned_or_failed"] += 1

    return list(channels.values())

