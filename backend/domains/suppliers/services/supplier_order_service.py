"""Supplier order operations service.

Owns the DB writes for supplier order status transitions. Routers and
controllers must not mutate the session directly for these operations.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import Order, OrderItem, SupplierProfile
import structlog
logger = structlog.get_logger(__name__)


def get_supplier_profile_by_user_id(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile owned by a user, raising 404 if absent."""
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404)
    return profile


def list_supplier_orders(db: Session, supplier_id: int) -> list[Order]:
    """Return distinct orders containing the supplier's items."""
    return (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .all()
    )


def get_supplier_order(db: Session, order_id: int, supplier_id: int) -> Order:
    """Return a supplier-owned order, raising 404 if not found."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")
    return order


def get_supplier_order_for_verify(db: Session, order_id: int, user_id: int) -> Order:
    """Return a supplier-owned order for parcel verification (joins product)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .join(OrderItem)
        .join(OrderItem.product)
        .filter(OrderItem.product.has(supplier_id=user_id))
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")
    return order


def get_supplier_order_items(db: Session, order_id: int, supplier_id: int) -> list[OrderItem]:
    """Return the supplier's items for an order."""
    return (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id, OrderItem.supplier_id == supplier_id)
        .all()
    )


def list_supplier_order_ids(db: Session, supplier_id: int) -> list[int]:
    """Return all order ids containing the supplier's items."""
    return [
        row[0]
        for row in db.query(Order.id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier_id)
        .distinct()
        .all()
    ]


def get_supplier_order_items_for_verify(db: Session, order_id: int, user_id: int) -> list[OrderItem]:
    """Return supplier items for an order (joined with product) for verification."""
    return (
        db.query(OrderItem)
        .join(OrderItem.product)
        .filter(OrderItem.order_id == order_id, OrderItem.product.has(supplier_id=user_id))
        .all()
    )


def resolve_shipment_info(db: Session, order_id: int) -> dict[str, Any]:
    """Resolve shipment info from the logistics models if available."""
    try:
        from _legacy.models import Shipment

        shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
        if not shipment:
            return {"has_shipment": False}

        return {
            "has_shipment": True,
            "shipment_id": shipment.id,
            "shipment_status": getattr(shipment, "status", "pending"),
            "shipment_status_label": getattr(shipment, "status", "pending").replace("_", " ").title(),
            "tracking_number": getattr(shipment, "tracking_number", None),
            "carrier_name": getattr(shipment, "carrier", None),
            "current_hub": getattr(shipment, "current_hub", None),
            "package_count": getattr(shipment, "package_count", None),
            "package_weight_kg": getattr(shipment, "package_weight_kg", None),
            "package_dimensions": getattr(shipment, "package_dimensions", None),
            "packaging_notes": getattr(shipment, "packaging_notes", None),
            "packaged_at": getattr(shipment, "packaged_at", None),
        }
    except Exception:
        logger.warning("Could not resolve shipment info for order %s", order_id)
        return {"has_shipment": False}


def mark_order_prepared_if_processing(order: Order, db: Session) -> bool:
    """Transition an order from 'processing' to 'prepared' and commit.

    Returns True if the status changed, False if it was not in 'processing'.
    """
    if order.status == "processing":
        order.status = "prepared"
        db.commit()
        return True
    return False
