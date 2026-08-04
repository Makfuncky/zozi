"""
Order Tracking Service — manages the full order lifecycle status transitions,
QR code generation for packages, event logging, and cross-panel visibility.

Status flow:
  Pending → Processing (supplier sees it) → Prepared (packaged + QR) →
  Picking Up (logistics confirmed) → Picked From Supplier (QR scanned) →
  In Transit → Delivered

Logistics sub-statuses (within In Transit):
  Logistic Received → Distribution Checkpoint → Out for Delivery → Delivered

Fault states:
  Shipment Delayed, Shipment Failed, Shipment Rescheduled,
  Shipment Cancelled, Shipment Returned
"""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from data.models import Order, OrderItem, Shipment, ShipmentEvent, User, LogisticsPartner, Notification
from utils.config import settings
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────

ORDER_STATUS_FLOW = [
    "pending",
    "processing",
    "prepared",
    "picking_up",
    "shipped",
    "in_transit",
    "delivered",
]

LOGISTICS_SUB_STATUSES = [
    "logistics_received",
    "distribution_checkpoint",
    "out_for_delivery",
]

FAULT_STATUSES = [
    "shipment_delayed",
    "shipment_failed",
    "shipment_rescheduled",
    "shipment_cancelled",
    "shipment_returned",
]

TERMINAL_STATUSES = {"delivered", "cancelled", "refunded", "failed", "shipment_cancelled", "shipment_returned"}

QR_SECRET = settings.secret_key or "zozi-order-qr-default"

# ── QR Code Generation ──────────────────────────────────────────────

def generate_order_qr(order_id: int, order_number: str) -> str:
    """Generate a scannable QR code string for an order package."""
    nonce = secrets.token_hex(8)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    payload = f"ZOZI:ORDER:{order_id}:{order_number}:{nonce}:{timestamp}"
    signature = hmac.new(
        QR_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    return f"{payload}:{signature}"


def validate_order_qr(qr_string: str) -> dict:
    """Validate a scanned QR code and return order info."""
    try:
        parts = qr_string.split(":")
        if len(parts) != 7 or parts[0] != "ZOZI" or parts[1] != "ORDER":
            return {"valid": False, "error": "Invalid QR format"}
        order_id = int(parts[2])
        order_number = parts[3]
        nonce = parts[4]
        timestamp = int(parts[5])
        signature = parts[6]

        # Verify signature
        payload = f"ZOZI:ORDER:{order_id}:{order_number}:{nonce}:{timestamp}"
        expected = hmac.new(
            QR_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if not hmac.compare_digest(signature, expected):
            return {"valid": False, "error": "Invalid QR signature"}

        # Check expiry (30 days)
        now = int(datetime.now(timezone.utc).timestamp())
        if now - timestamp > 30 * 24 * 3600:
            return {"valid": False, "error": "QR code expired"}

        return {
            "valid": True,
            "order_id": order_id,
            "order_number": order_number,
        }
    except (ValueError, IndexError) as e:
        return {"valid": False, "error": str(e)}


# ── Status Transition Validity ──────────────────────────────────────

def _can_transition(from_status: str, to_status: str) -> bool:
    """Check if a status transition is valid in the order lifecycle."""
    if from_status == to_status:
        return True

    # Forward flow
    flow_map = {
        "pending": ["processing", "cancelled"],
        "processing": ["prepared", "cancelled"],
        "prepared": ["picking_up", "processing", "cancelled"],
        "picking_up": ["shipped", "prepared", "cancelled"],
        "shipped": ["in_transit", "delivered", "cancelled"],
        "in_transit": LOGISTICS_SUB_STATUSES + ["delivered"] + FAULT_STATUSES,
        "delivered": ["shipment_returned"],
    }

    allowed = flow_map.get(from_status, [])
    if to_status in allowed:
        return True

    # Admin override: any non-terminal to any non-terminal
    if to_status not in TERMINAL_STATUSES:
        return True

    return False


def _log_status_event(
    db: Session,
    shipment: Shipment,
    order: Order,
    actor_user_id: int,
    actor_role: str,
    event_type: str,
    status_after: str,
    notes: Optional[str] = None,
    location: Optional[str] = None,
    scan_code: Optional[str] = None,
) -> ShipmentEvent:
    """Create a shipment event record."""
    now = _utcnow()
    event = ShipmentEvent(
        shipment_id=shipment.id,
        order_id=order.id,
        supplier_id=shipment.supplier_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        event_type=event_type,
        status_after=status_after,
        location=location,
        scan_code=scan_code or shipment.scan_code,
        notes=notes or f"Status changed to {status_after}",
        created_at=now,
        country_code=getattr(order, "country_code", None),
    )
    db.add(event)
    return event


def _notify_party(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None,
) -> None:
    """Send a notification to a user."""
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


# ── Supplier Actions ───────────────────────────────────────────────

def supplier_process_order(
    db: Session,
    order_id: int,
    supplier_user_id: int,
) -> dict:
    """Supplier starts processing an order. Status: Pending → Processing."""
    order, shipment = _get_order_and_shipment(db, order_id, supplier_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found for this supplier"}

    if order.status not in ("pending", "confirmed"):
        return {"success": False, "error": f"Cannot process order in '{order.status}' status"}

    order.status = "processing"
    order.updated_at = _utcnow()
    shipment.status = "processing"
    shipment.updated_at = _utcnow()

    _log_status_event(db, shipment, order, supplier_user_id, "supplier",
                       "supplier_prepared", "processing",
                       notes="Supplier started processing the order")

    _notify_party(db, order.user_id, "Order Processing",
                   f"Order #{order.id} is now being processed by the supplier.",
                   link=f"/orders/{order.id}")

    db.commit()
    return {"success": True, "order_id": order.id, "status": "processing"}


def supplier_prepare_order(
    db: Session,
    order_id: int,
    supplier_user_id: int,
    package_weight: Optional[float] = None,
    package_dimensions: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Supplier marks order as prepared/packaged. Status: Processing → Prepared.
    Generates QR code for the package and creates a scanable label."""
    order, shipment = _get_order_and_shipment(db, order_id, supplier_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found for this supplier"}

    if order.status not in ("processing",):
        return {"success": False, "error": f"Cannot prepare order in '{order.status}' status"}

    # Generate QR code
    qr_code = generate_order_qr(order.id, order.order_number or f"ORD-{order.id}")
    shipment.scan_code = qr_code
    shipment.status = "prepared"
    shipment.packaged_at = _utcnow()
    shipment.packaged_by_user_id = supplier_user_id
    if package_weight:
        shipment.package_weight_kg = package_weight
    if package_dimensions:
        shipment.package_dimensions = package_dimensions
    if notes:
        shipment.packaging_notes = notes
    shipment.updated_at = _utcnow()

    order.status = "prepared"
    order.updated_at = _utcnow()

    _log_status_event(db, shipment, order, supplier_user_id, "supplier",
                       "supplier_prepared", "prepared",
                       notes=notes or "Supplier packaged and prepared the order",
                       scan_code=qr_code)

    _notify_party(db, order.user_id, "Order Prepared",
                   f"Order #{order.id} has been packaged and ready for pickup.",
                   link=f"/orders/{order.id}")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": "prepared",
        "qr_code": qr_code,
    }


# ── Logistics Actions ──────────────────────────────────────────────

def logistics_confirm_pickup(
    db: Session,
    order_id: int,
    logistics_user_id: int,
) -> dict:
    """Logistics partner confirms they will pick up. Status: Prepared → Picking Up.
    Removes from other logistics partners' available lists."""
    return _logistics_status_transition(db, order_id, logistics_user_id,
                                         "prepared", "picking_up",
                                         "pickup_confirmed",
                                         "Logistics partner confirmed for pickup")


def logistics_scan_and_receive(
    db: Session,
    order_id: int,
    logistics_user_id: int,
    scan_code: str,
    location: Optional[str] = None,
) -> dict:
    """Logistics partner scans QR and receives package from supplier.
    Status: Picking Up → Shipped (Picked From Supplier)."""
    # Validate QR code
    qr_result = validate_order_qr(scan_code)
    if not qr_result.get("valid"):
        # Allow non-QR scan codes too (order number, etc.)
        pass

    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}

    if order.status not in ("prepared", "picking_up"):
        return {"success": False, "error": f"Cannot pick up order in '{order.status}' status"}

    shipment.status = "shipped"
    shipment.shipped_at = _utcnow()
    shipment.current_hub = location or shipment.current_hub
    shipment.scan_code = scan_code
    shipment.updated_at = _utcnow()

    order.status = "shipped"
    order.updated_at = _utcnow()

    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner",
                       "picked_from_supplier", "shipped",
                       notes=f"Package picked from supplier. Scan: {scan_code}",
                       location=location,
                       scan_code=scan_code)

    _notify_party(db, order.user_id, "Order Picked Up",
                   f"Order #{order.id} has been picked up by logistics partner.",
                   link=f"/orders/{order.id}")

    # Notify supplier
    supplier_user = db.query(User).filter(User.id == shipment.supplier_id).first()
    if supplier_user:
        _notify_party(db, shipment.supplier_id, "Package Collected",
                       f"Order #{order.id} has been collected by logistics.",
                       link=f"/supplier/orders/{order.id}")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": "shipped",
        "event": "picked_from_supplier",
    }


def logistics_update_transit_status(
    db: Session,
    order_id: int,
    logistics_user_id: int,
    event_type: str,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Logistics partner updates transit sub-status. Valid types:
    logistics_received, distribution_checkpoint, out_for_delivery,
    shipment_delayed, shipment_failed, shipment_rescheduled."""
    if event_type not in LOGISTICS_SUB_STATUSES + FAULT_STATUSES:
        return {"success": False, "error": f"Invalid event type: {event_type}"}

    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}

    if order.status not in ("shipped", "in_transit"):
        return {"success": False, "error": "Cannot update transit in '" + str(order.status) + "' status"}

    # Map event type to status
    status_map = {
        "logistics_received": "in_transit",
        "distribution_checkpoint": "in_transit",
        "out_for_delivery": "in_transit",
        "shipment_delayed": "in_transit",
        "shipment_failed": "failed",
        "shipment_rescheduled": "in_transit",
    }
    new_status = status_map.get(event_type, "in_transit")

    if location:
        shipment.current_hub = location
    shipment.status = new_status
    shipment.updated_at = _utcnow()

    if new_status == "failed":
        order.status = "failed"
    else:
        order.status = new_status
    order.updated_at = _utcnow()

    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner",
                       event_type, new_status,
                       notes=notes, location=location)

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": new_status,
        "event": event_type,
    }


def logistics_deliver_order(
    db: Session,
    order_id: int,
    logistics_user_id: int,
    signature_name: Optional[str] = None,
    signature_data_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Logistics partner delivers order to customer.
    Status: In Transit → Delivered. Captures e-signature."""
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}

    if order.status not in ("shipped", "in_transit"):
        return {"success": False, "error": f"Cannot deliver order in '{order.status}' status"}

    now = _utcnow()
    shipment.status = "delivered"
    shipment.actual_delivery = now
    if signature_name:
        shipment.delivery_signature_name = signature_name
    if signature_data_url:
        shipment.delivery_signature_data_url = signature_data_url
    shipment.delivery_signature_captured_at = now
    shipment.updated_at = now

    order.status = "delivered"
    order.updated_at = now

    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner",
                       "customer_received", "delivered",
                       notes=notes or "Package delivered to customer")

    _notify_party(db, order.user_id, "Order Delivered",
                   f"Order #{order.id} has been delivered successfully!",
                   link=f"/orders/{order.id}")

    # Notify supplier
    _notify_party(db, shipment.supplier_id, "Delivery Complete",
                   f"Order #{order.id} has been delivered to customer.",
                   link=f"/supplier/orders/{order.id}")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": "delivered",
        "delivered_at": now.isoformat(),
    }


def logistics_cancel_pickup(
    db: Session,
    order_id: int,
    logistics_user_id: int,
    reason: Optional[str] = None,
) -> dict:
    """Logistics partner cancels pickup before shipped status.
    Order goes back to 'prepared' for other logistics partners to pick up."""
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}

    if order.status not in ("prepared", "picking_up"):
        return {"success": False, "error": f"Cannot cancel pickup in '{order.status}' status"}

    shipment.status = "prepared"
    shipment.updated_at = _utcnow()
    order.status = "prepared"
    order.updated_at = _utcnow()

    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner",
                       "pickup_cancelled", "prepared",
                       notes=reason or "Logistics partner cancelled pickup")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": "prepared",
        "event": "pickup_cancelled",
    }


# ── Admin Actions ──────────────────────────────────────────────────

def admin_override_status(
    db: Session,
    order_id: int,
    new_status: str,
    admin_user_id: int,
    reason: Optional[str] = None,
) -> dict:
    """Admin can override order status at any stage."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "error": "Order not found"}

    old_status = order.status
    order.status = new_status
    order.updated_at = _utcnow()

    # Update any shipments too
    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    for shipment in shipments:
        shipment.status = new_status
        shipment.updated_at = _utcnow()
        _log_status_event(db, shipment, order, admin_user_id, "admin",
                           "status_manual_update", new_status,
                           notes=reason or f"Admin overrode status: {old_status} → {new_status}")

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "old_status": old_status,
        "new_status": new_status,
    }


def admin_cancel_order(
    db: Session,
    order_id: int,
    admin_user_id: int,
    reason: Optional[str] = None,
) -> dict:
    """Admin can cancel any order at any stage."""
    return admin_override_status(db, order_id, "cancelled", admin_user_id,
                                  reason=reason or "Cancelled by admin")


# ── Customer Actions ───────────────────────────────────────────────

def customer_cancel_order(
    db: Session,
    order_id: int,
    customer_user_id: int,
) -> dict:
    """Customer can cancel order only in pending/processing/prepared status."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == customer_user_id,
    ).first()
    if not order:
        return {"success": False, "error": "Order not found"}

    if order.status not in ("pending", "confirmed", "processing", "prepared"):
        return {"success": False, "error":
                f"Cannot cancel order in '{order.status}' status. "
                "Only pending, confirmed, processing, or prepared orders can be cancelled."}

    old_status = order.status
    order.status = "cancelled"
    order.updated_at = _utcnow()

    shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    for shipment in shipments:
        shipment.status = "cancelled"
        shipment.updated_at = _utcnow()
        _log_status_event(db, shipment, order, customer_user_id, "customer",
                           "cancelled", "cancelled",
                           notes=f"Customer cancelled order from {old_status}")

    _notify_party(db, shipment.supplier_id, "Order Cancelled",
                   f"Order #{order.id} has been cancelled by the customer.",
                   link=f"/supplier/orders/{order.id}") if shipments else None

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": "cancelled",
    }


# ── Helpers ─────────────────────────────────────────────────────────

def _get_order_and_shipment(db: Session, order_id: int, supplier_user_id: int):
    """Get order and shipment for a supplier."""
    order = (
        db.query(Order)
        .join(OrderItem)
        .filter(
            Order.id == order_id,
            OrderItem.supplier_id == supplier_user_id,
        )
        .first()
    )
    if not order:
        return None, None
    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.order_id == order_id,
            Shipment.supplier_id == supplier_user_id,
        )
        .first()
    )
    return order, shipment


def _get_order_for_logistics(db: Session, order_id: int, logistics_user_id: int):
    """Get order and shipment for a logistics partner."""
    partner = db.query(LogisticsPartner).filter(
        LogisticsPartner.user_id == logistics_user_id
    ).first()
    if not partner:
        return None, None
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None, None
    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.order_id == order_id,
            Shipment.assigned_partner_id == partner.id,
        )
        .first()
    )
    return order, shipment


def _logistics_status_transition(
    db: Session,
    order_id: int,
    logistics_user_id: int,
    from_status: str,
    to_status: str,
    event_type: str,
    notes: str,
) -> dict:
    """Generic status transition for logistics actions."""
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}

    if order.status != from_status:
        return {"success": False,
                "error": f"Cannot transition from '{order.status}' to '{to_status}'. "
                         f"Expected '{from_status}'."}

    shipment.status = to_status
    shipment.updated_at = _utcnow()
    order.status = to_status
    order.updated_at = _utcnow()

    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner",
                       event_type, to_status, notes=notes)

    db.commit()

    return {
        "success": True,
        "order_id": order.id,
        "status": to_status,
        "event": event_type,
    }


# ── Cross-Panel Visibility ─────────────────────────────────────────

def get_available_orders_for_logistics(db: Session) -> list[dict]:
    """Return all orders in 'prepared' status available for logistics pickup."""
    orders = (
        db.query(Order)
        .filter(Order.status == "prepared")
        .order_by(Order.updated_at.desc())
        .all()
    )
    result = []
    for order in orders:
        shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
        result.append({
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "customer_name": order.user.username if order.user else "Unknown",
            "shipping_address": order.shipping_address,
            "delivery_location": order.delivery_location,
            "scan_code": shipment.scan_code if shipment else None,
            "supplier_id": shipment.supplier_id if shipment else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "prepared_at": shipment.packaged_at.isoformat() if shipment and shipment.packaged_at else None,
        })
    return result


def get_order_shipment_label(order_id: int, db: Session) -> Optional[dict]:
    """Return complete packing label data for printing."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None

    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    customer = order.user
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    return {
        "order_id": order.id,
        "order_number": order.order_number or f"ORD-{order.id}",
        "status": order.status,
        "qr_code": shipment.scan_code if shipment else None,
        "customer": {
            "name": customer.full_name or customer.username if customer else "Unknown",
            "phone": order.customer_phone,
            "email": customer.email if customer else None,
            "address": order.shipping_address,
            "city": order.shipping_city,
            "country": order.shipping_country,
            "postal_code": order.shipping_postal_code,
            "delivery_location": order.delivery_location,
            "delivery_note": order.delivery_note,
        },
        "items": [
            {
                "product_name": item.product_name or f"Product #{item.product_id}",
                "quantity": item.quantity,
                "price": float(item.price or 0),
                "total": float((item.price or 0) * item.quantity),
                "variant": (item.selected_size or "") + " " + (item.selected_color or ""),
            }
            for item in items
        ],
        "totals": {
            "subtotal": float(order.subtotal_amount or 0),
            "shipping": float(order.shipping_amount or 0),
            "discount": float(order.discount_amount or 0),
            "tax": float(order.tax_amount or 0),
            "total": float(order.total_amount or 0),
        },
        "payment_method": order.payment_method,
        "ordered_at": order.created_at.isoformat() if order.created_at else None,
        "shipment": {
            "tracking_number": shipment.tracking_number if shipment else None,
            "package_weight_kg": float(shipment.package_weight_kg) if shipment and shipment.package_weight_kg else None,
            "package_dimensions": shipment.package_dimensions if shipment else None,
            "packaged_at": shipment.packaged_at.isoformat() if shipment and shipment.packaged_at else None,
        } if shipment else None,
    }
