"""Supplier Packing Service — supplier packing confirmation workflow.

Manages the supplier-side packing process: confirming items are packed,
generating QR codes for packages, recording package dimensions/weight,
and transitioning order status from 'processing' to 'prepared'.

Wiring:
    orders/services/packing/ → providers/suppliers/ (supplier notification)
    orders/services/packing/ → infrastructure/messaging/ (status update events)
    orders/services/packing/ → orders/services/tracking/ (status transition)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.logistics.models.logistics import Shipment
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from infrastructure.utils.config import settings
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

PACKING_SECRET = settings.secret_key
if not PACKING_SECRET:
    raise ValueError("settings.secret_key must be configured")

# ── QR Code Generation ──────────────────────────────────────────────────────


def generate_packing_qr(order_id: int, shipment_id: int) -> str:
    """Generate a scannable QR code string for a packed shipment."""
    nonce = secrets.token_hex(8)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    payload = f"ZOZI:PACK:{order_id}:{shipment_id}:{nonce}:{timestamp}"
    signature = hmac.new(
        PACKING_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{payload}:{signature}"


def validate_packing_qr(qr_string: str) -> dict:
    """Validate a scanned packing QR code and return info."""
    try:
        parts = qr_string.split(":")
        if len(parts) != 6 or parts[0] != "ZOZI" or parts[1] != "PACK":
            return {"valid": False, "error": "Invalid QR format"}
        order_id = int(parts[2])
        shipment_id = int(parts[3])
        nonce = parts[4]
        timestamp = int(parts[5])

        payload = f"ZOZI:PACK:{order_id}:{shipment_id}:{nonce}"
        expected = hmac.new(
            PACKING_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if not hmac.compare_digest(timestamp, expected):
            return {"valid": False, "error": "Invalid QR signature"}

        return {
            "valid": True,
            "order_id": order_id,
            "shipment_id": shipment_id,
        }
    except (ValueError, IndexError) as e:
        return {"valid": False, "error": str(e)}


# ── Supplier Packing Confirmation ────────────────────────────────────────────


def supplier_confirm_packing(
    db: Session,
    order_id: int,
    supplier_user_id: int,
    package_weight_kg: Optional[float] = None,
    package_dimensions: Optional[str] = None,
    package_count: int = 1,
    notes: Optional[str] = None,
) -> dict:
    """Supplier confirms order is packed and ready for pickup.

    Status transition: processing → prepared.
    Generates QR code, records package details, notifies logistics.
    """
    order, shipment = _get_order_and_shipment(db, order_id, supplier_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found for this supplier"}

    if order.status != "processing":
        return {"success": False, "error": f"Cannot pack order in '{order.status}' status"}

    # Generate packing QR
    qr_code = generate_packing_qr(order.id, shipment.id)

    # Update shipment
    shipment.scan_code = qr_code
    shipment.status = "prepared"
    shipment.packaged_at = _utcnow()
    shipment.packaged_by_user_id = supplier_user_id
    shipment.package_count = package_count
    if package_weight_kg:
        shipment.package_weight_kg = package_weight_kg
    if package_dimensions:
        shipment.package_dimensions = package_dimensions
    if notes:
        shipment.packaging_notes = notes
    shipment.updated_at = _utcnow()

    # Update order
    order.status = "prepared"
    order.updated_at = _utcnow()

    # Log event
    _log_packing_event(db, shipment, order, supplier_user_id, "packed", "prepared", notes)

    # Notify customer
    _notify_party(db, order.user_id, "Order Packed",
                  f"Order #{order.id} has been packed and is ready for pickup.",
                  link=f"/orders/{order.id}")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "shipment_id": shipment.id,
        "status": "prepared",
        "qr_code": qr_code,
        "package_count": package_count,
    }


def get_packing_status(
    db: Session,
    order_id: int,
    supplier_user_id: int,
) -> dict:
    """Get current packing status for a supplier's order."""
    order = (
        db.query(Order)
        .join(OrderItem)
        .filter(Order.id == order_id, OrderItem.supplier_id == supplier_user_id)
        .first()
    )
    if not order:
        return {"success": False, "error": "Order not found"}

    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_user_id)
        .first()
    )

    return {
        "success": True,
        "order_id": order.id,
        "order_status": order.status,
        "is_packed": order.status in ("prepared", "picking_up", "shipped", "in_transit", "delivered"),
        "shipment_id": shipment.id if shipment else None,
        "qr_code": shipment.scan_code if shipment else None,
        "packaged_at": shipment.packaged_at.isoformat() if shipment and shipment.packaged_at else None,
        "package_weight_kg": float(shipment.package_weight_kg) if shipment and shipment.package_weight_kg else None,
        "package_dimensions": shipment.package_dimensions if shipment else None,
    }


def list_orders_awaiting_packing(db: Session, supplier_user_id: int) -> list[dict]:
    """List orders that need packing by this supplier (status=processing)."""
    orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(
            OrderItem.supplier_id == supplier_user_id,
            Order.status == "processing",
        )
        .distinct()
        .order_by(Order.created_at.asc())
        .all()
    )
    return [
        {
            "order_id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "item_count": len(o.items),
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


# ── Internal Helpers ─────────────────────────────────────────────────────────


def _get_order_and_shipment(db: Session, order_id: int, supplier_user_id: int):
    """Get order and shipment for a supplier."""
    order = (
        db.query(Order)
        .join(OrderItem)
        .filter(Order.id == order_id, OrderItem.supplier_id == supplier_user_id)
        .first()
    )
    if not order:
        return None, None
    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_user_id)
        .first()
    )
    return order, shipment


def _log_packing_event(
    db: Session,
    shipment: Shipment,
    order: Order,
    actor_user_id: int,
    event_type: str,
    status_after: str,
    notes: Optional[str] = None,
) -> None:
    """Log a packing status event."""
    from domains.logistics.models.logistics import ShipmentEvent
    event = ShipmentEvent(
        shipment_id=shipment.id,
        order_id=order.id,
        supplier_id=shipment.supplier_id,
        actor_user_id=actor_user_id,
        actor_role="supplier",
        event_type=event_type,
        status_after=status_after,
        notes=notes or f"Packing status: {status_after}",
        created_at=_utcnow(),
        country_code=getattr(order, "country_code", None),
    )
    db.add(event)


def _notify_party(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None,
) -> None:
    """Send a notification to a user."""
    from domains.comms.models.communication import Notification
    try:
        notification = Notification(
            user_id=user_id,
            type="order_update",
            title=title,
            message=message,
            link=link,
        )
        db.add(notification)
    except Exception as e:
        logger.warning("Failed to create notification: %s", e)
