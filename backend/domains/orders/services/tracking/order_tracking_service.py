"""
Orders — Order Tracking Service (canonical).

Merged from:
  - domains/orders/services/order_tracking_service.py
  - domains/orders/services/orders_order_tracking_service.py (re-export delegator)

Manages the full order lifecycle status transitions, QR code generation,
event logging, and cross-panel visibility.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException
from domains.governance.models.user import User
from domains.comms.models.communication import Notification
from domains.logistics.models.logistics import Shipment, ShipmentEvent, LogisticsPartner
from domains.orders.models.orders import Order, OrderItem
from infrastructure.utils.config import settings
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

ORDER_STATUS_FLOW = ["pending", "processing", "prepared", "picking_up", "shipped", "in_transit", "delivered"]
LOGISTICS_SUB_STATUSES = ["logistics_received", "distribution_checkpoint", "out_for_delivery"]
FAULT_STATUSES = ["shipment_delayed", "shipment_failed", "shipment_rescheduled", "shipment_cancelled", "shipment_returned"]
TERMINAL_STATUSES = {"delivered", "cancelled", "refunded", "failed", "shipment_cancelled", "shipment_returned"}
QR_SECRET = settings.secret_key or "zozi-order-qr-default"


def generate_order_qr(order_id: int, order_number: str) -> str:
    nonce = secrets.token_hex(8)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    payload = f"ZOZI:ORDER:{order_id}:{order_number}:{nonce}:{timestamp}"
    signature = hmac.new(QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{payload}:{signature}"


def validate_order_qr(qr_string: str) -> dict:
    try:
        parts = qr_string.split(":")
        if len(parts) != 7 or parts[0] != "ZOZI" or parts[1] != "ORDER":
            return {"valid": False, "error": "Invalid QR format"}
        order_id, order_number, nonce, timestamp = int(parts[2]), parts[3], parts[4], int(parts[5])
        signature = parts[6]
        payload = f"ZOZI:ORDER:{order_id}:{order_number}:{nonce}:{timestamp}"
        expected = hmac.new(QR_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(signature, expected):
            return {"valid": False, "error": "Invalid QR signature"}
        if int(datetime.now(timezone.utc).timestamp()) - timestamp > 30 * 24 * 3600:
            return {"valid": False, "error": "QR code expired"}
        return {"valid": True, "order_id": order_id, "order_number": order_number}
    except (ValueError, IndexError) as e:
        return {"valid": False, "error": str(e)}


def _can_transition(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return True
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
    return to_status in allowed or (to_status not in TERMINAL_STATUSES)


def _log_status_event(db, shipment, order, actor_user_id, actor_role, event_type, status_after, notes=None, location=None, scan_code=None):
    event = ShipmentEvent(
        shipment_id=shipment.id, order_id=order.id, supplier_id=shipment.supplier_id,
        actor_user_id=actor_user_id, actor_role=actor_role, event_type=event_type,
        status_after=status_after, location=location, scan_code=scan_code or shipment.scan_code,
        notes=notes or f"Status changed to {status_after}", created_at=_utcnow(),
        country_code=getattr(order, "country_code", None),
    )
    db.add(event)
    return event


def _notify_party(db, user_id, title, message, link=None):
    try:
        db.add(Notification(user_id=user_id, type="order_update", title=title, message=message, link=link))
    except Exception as e:
        logger.warning("Failed to create notification: %s", e)


def _get_order_and_shipment(db, order_id, supplier_user_id):
    order = db.query(Order).join(OrderItem).filter(Order.id == order_id, OrderItem.supplier_id == supplier_user_id).first()
    if not order:
        return None, None
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id, Shipment.supplier_id == supplier_user_id).first()
    return order, shipment


def _get_order_for_logistics(db, order_id, logistics_user_id):
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == logistics_user_id).first()
    if not partner:
        return None, None
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None, None
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id, Shipment.assigned_partner_id == partner.id).first()
    return order, shipment


def _logistics_status_transition(db, order_id, logistics_user_id, from_status, to_status, event_type, notes):
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}
    if order.status != from_status:
        return {"success": False, "error": f"Cannot transition from '{order.status}' to '{to_status}'. Expected '{from_status}'."}
    shipment.status = to_status
    shipment.updated_at = _utcnow()
    order.status = to_status
    order.updated_at = _utcnow()
    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner", event_type, to_status, notes=notes)
    db.commit()
    return {"success": True, "order_id": order.id, "status": to_status, "event": event_type}


# ── Supplier Actions ───────────────────────────────────────────────

def supplier_process_order(db, order_id, supplier_user_id):
    order, shipment = _get_order_and_shipment(db, order_id, supplier_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found for this supplier"}
    if order.status not in ("pending", "confirmed"):
        return {"success": False, "error": f"Cannot process order in '{order.status}' status"}
    order.status = "processing"
    order.updated_at = _utcnow()
    shipment.status = "processing"
    shipment.updated_at = _utcnow()
    _log_status_event(db, shipment, order, supplier_user_id, "supplier", "supplier_prepared", "processing", notes="Supplier started processing the order")
    _notify_party(db, order.user_id, "Order Processing", f"Order #{order.id} is now being processed by the supplier.", link=f"/orders/{order.id}")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "processing"}


def supplier_prepare_order(db, order_id, supplier_user_id, package_weight=None, package_dimensions=None, notes=None):
    order, shipment = _get_order_and_shipment(db, order_id, supplier_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found for this supplier"}
    if order.status not in ("processing",):
        return {"success": False, "error": f"Cannot prepare order in '{order.status}' status"}
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
    _log_status_event(db, shipment, order, supplier_user_id, "supplier", "supplier_prepared", "prepared", notes=notes or "Supplier packaged and prepared the order", scan_code=qr_code)
    _notify_party(db, order.user_id, "Order Prepared", f"Order #{order.id} has been packaged and ready for pickup.", link=f"/orders/{order.id}")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "prepared", "qr_code": qr_code}


# ── Logistics Actions ──────────────────────────────────────────────

def logistics_confirm_pickup(db, order_id, logistics_user_id):
    return _logistics_status_transition(db, order_id, logistics_user_id, "prepared", "picking_up", "pickup_confirmed", "Logistics partner confirmed for pickup")


def logistics_scan_and_receive(db, order_id, logistics_user_id, scan_code, location=None):
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
    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner", "picked_from_supplier", "shipped", notes=f"Package picked from supplier. Scan: {scan_code}", location=location, scan_code=scan_code)
    _notify_party(db, order.user_id, "Order Picked Up", f"Order #{order.id} has been picked up by logistics partner.", link=f"/orders/{order.id}")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "shipped", "event": "picked_from_supplier"}


def logistics_update_transit_status(db, order_id, logistics_user_id, event_type, location=None, notes=None):
    if event_type not in LOGISTICS_SUB_STATUSES + FAULT_STATUSES:
        return {"success": False, "error": f"Invalid event type: {event_type}"}
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}
    if order.status not in ("shipped", "in_transit"):
        return {"success": False, "error": f"Cannot update transit in '{order.status}' status"}
    status_map = {"logistics_received": "in_transit", "distribution_checkpoint": "in_transit", "out_for_delivery": "in_transit", "shipment_delayed": "in_transit", "shipment_failed": "failed", "shipment_rescheduled": "in_transit"}
    new_status = status_map.get(event_type, "in_transit")
    if location:
        shipment.current_hub = location
    shipment.status = new_status
    shipment.updated_at = _utcnow()
    order.status = new_status
    order.updated_at = _utcnow()
    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner", event_type, new_status, notes=notes, location=location)
    db.commit()
    return {"success": True, "order_id": order.id, "status": new_status, "event": event_type}


def logistics_deliver_order(db, order_id, logistics_user_id, signature_name=None, signature_data_url=None, notes=None):
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
    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner", "customer_received", "delivered", notes=notes or "Package delivered to customer")
    _notify_party(db, order.user_id, "Order Delivered", f"Order #{order.id} has been delivered successfully!", link=f"/orders/{order.id}")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "delivered", "delivered_at": now.isoformat()}


def logistics_cancel_pickup(db, order_id, logistics_user_id, reason=None):
    order, shipment = _get_order_for_logistics(db, order_id, logistics_user_id)
    if not order or not shipment:
        return {"success": False, "error": "Order or shipment not found"}
    if order.status not in ("prepared", "picking_up"):
        return {"success": False, "error": f"Cannot cancel pickup in '{order.status}' status"}
    shipment.status = "prepared"
    shipment.updated_at = _utcnow()
    order.status = "prepared"
    order.updated_at = _utcnow()
    _log_status_event(db, shipment, order, logistics_user_id, "logistics_partner", "pickup_cancelled", "prepared", notes=reason or "Logistics partner cancelled pickup")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "prepared", "event": "pickup_cancelled"}


# ── Admin Actions ──────────────────────────────────────────────────

def admin_override_status(db, order_id, new_status, admin_user_id, reason=None):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "error": "Order not found"}
    old_status = order.status
    order.status = new_status
    order.updated_at = _utcnow()
    for shipment in db.query(Shipment).filter(Shipment.order_id == order_id).all():
        shipment.status = new_status
        shipment.updated_at = _utcnow()
        _log_status_event(db, shipment, order, admin_user_id, "admin", "status_manual_update", new_status, notes=reason or f"Admin overrode status: {old_status} → {new_status}")
    db.commit()
    return {"success": True, "order_id": order.id, "old_status": old_status, "new_status": new_status}


def admin_cancel_order(db, order_id, admin_user_id, reason=None):
    return admin_override_status(db, order_id, "cancelled", admin_user_id, reason=reason or "Cancelled by admin")


# ── Customer Actions ───────────────────────────────────────────────

def customer_cancel_order(db, order_id, customer_user_id):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == customer_user_id).first()
    if not order:
        return {"success": False, "error": "Order not found"}
    if order.status not in ("pending", "confirmed", "processing", "prepared"):
        return {"success": False, "error": f"Cannot cancel order in '{order.status}' status. Only pending, confirmed, processing, or prepared orders can be cancelled."}
    order.status = "cancelled"
    order.updated_at = _utcnow()
    for shipment in db.query(Shipment).filter(Shipment.order_id == order_id).all():
        shipment.status = "cancelled"
        shipment.updated_at = _utcnow()
        _log_status_event(db, shipment, order, customer_user_id, "customer", "cancelled", "cancelled", notes=f"Customer cancelled order from {order.status}")
    db.commit()
    return {"success": True, "order_id": order.id, "status": "cancelled"}


# ── Cross-Panel Visibility ─────────────────────────────────────────

def list_my_pickups(db, user_id):
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    if not partner:
        raise HTTPException(404, "Logistics partner profile not found")
    shipments = db.query(Shipment).filter(Shipment.assigned_partner_id == partner.id).order_by(Shipment.updated_at.desc()).all()
    return [{"id": s.id, "order_id": s.order_id, "status": s.status, "tracking_number": s.tracking_number, "scan_code": s.scan_code, "current_hub": s.current_hub, "package_weight_kg": float(s.package_weight_kg) if s.package_weight_kg else None, "packaged_at": s.packaged_at.isoformat() if s.packaged_at else None, "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None, "updated_at": s.updated_at.isoformat() if s.updated_at else None} for s in shipments]


def get_available_orders_for_logistics(db):
    orders = db.query(Order).filter(Order.status == "prepared").order_by(Order.updated_at.desc()).all()
    result = []
    for order in orders:
        shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
        result.append({"order_id": order.id, "order_number": order.order_number, "status": order.status, "customer_name": order.user.username if order.user else "Unknown", "shipping_address": order.shipping_address, "delivery_location": order.delivery_location, "scan_code": shipment.scan_code if shipment else None, "supplier_id": shipment.supplier_id if shipment else None, "created_at": order.created_at.isoformat() if order.created_at else None, "prepared_at": shipment.packaged_at.isoformat() if shipment and shipment.packaged_at else None})
    return result


def get_order_shipment_label(order_id, db):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    customer = order.user
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return {
        "order_id": order.id, "order_number": order.order_number or f"ORD-{order.id}", "status": order.status,
        "qr_code": shipment.scan_code if shipment else None,
        "customer": {"name": customer.full_name or customer.username if customer else "Unknown", "phone": order.customer_phone, "email": customer.email if customer else None, "address": order.shipping_address, "city": order.shipping_city, "country": order.shipping_country, "postal_code": order.shipping_postal_code, "delivery_location": order.delivery_location, "delivery_note": order.delivery_note},
        "items": [{"product_name": item.product_name or f"Product #{item.product_id}", "quantity": item.quantity, "price": float(item.price or 0), "total": float((item.price or 0) * item.quantity), "variant": f"{item.selected_size or ''} {item.selected_color or ''}".strip() or None} for item in items],
        "totals": {"subtotal": float(order.subtotal_amount or 0), "shipping": float(order.shipping_amount or 0), "discount": float(order.discount_amount or 0), "tax": float(order.tax_amount or 0), "total": float(order.total_amount or 0)},
        "payment_method": order.payment_method,
        "ordered_at": order.created_at.isoformat() if order.created_at else None,
        "shipment": {"tracking_number": shipment.tracking_number if shipment else None, "package_weight_kg": float(shipment.package_weight_kg) if shipment and shipment.package_weight_kg else None, "package_dimensions": shipment.package_dimensions if shipment else None, "packaged_at": shipment.packaged_at.isoformat() if shipment and shipment.packaged_at else None} if shipment else None,
    }
