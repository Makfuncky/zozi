"""
Supplier Orders Service
=======================
Owns the DB work that previously lived in ``routers/supplier/supplier_orders.py``
so that router stays a thin delegator (layering: LC1/W1).

Covers:
  - Supplier order listing
  - Packing-sheet / label data (incl. shipment resolution)
  - Ownership checks used by the parcel-proof endpoints
  - Order status transition after a parcel proof upload
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Order, OrderItem, SupplierProfile, User
from data.services_write_helpers import commit_only
from services.storage import storage as _storage

logger = logging.getLogger(__name__)


def delete_parcel_proof_files(db: Session, order_id: int) -> None:
    """Remove all existing reference_* files from parcel-proof storage for the given order."""
    prefix = f"parcel_proofs/{order_id}/"
    for old_ref in _storage.list(prefix):
        if old_ref.split("/")[-1].startswith("reference_"):
            try:
                _storage.delete(old_ref)
            except Exception:
                pass


# ── Helper: extract user ID from either a dict or a User ORM model ─────
def get_user_id(current_user: User | dict) -> int:
    """`require_supplier` may return a dict or a User ORM model.
    This helper normalises both to an int ID."""
    if isinstance(current_user, dict):
        uid = current_user.get("id") or current_user.get("user_id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid user session: missing user ID")
        return int(uid)
    return current_user.id


def get_user_attr(current_user: User | dict, attr: str, default: Any = "") -> Any:
    """Safe attribute access for both dict and ORM current_user."""
    if isinstance(current_user, dict):
        return current_user.get(attr, default)
    return getattr(current_user, attr, default)


def _require_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile owned by ``user_id`` (404 if absent)."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return supplier


def _require_supplier_order(db: Session, order_id: int, supplier_id: int) -> Order:
    """Return an order containing at least one item from ``supplier_id`` (404 otherwise)."""
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


def list_orders_for_supplier(
    db: Session, current_user: User | dict, skip: int = 0, limit: int = 20
) -> list[Order]:
    """Return a page of orders that contain items sold by this supplier."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == get_user_id(current_user))
        .first()
    )
    if not supplier:
        raise HTTPException(404)
    orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
        .offset(skip).limit(limit)
        .all()
    )
    return orders


def resolve_shipment_info(
    db: Session, order_id: int, supplier_id: int
) -> dict[str, Any]:
    """Resolve shipment info from the logistics models if available."""
    try:
        from data.models import Shipment

        shipment = (
            db.query(Shipment)
            .filter(
                Shipment.order_id == order_id,
            )
            .first()
        )
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


def get_supplier_order_label(
    db: Session, current_user: User | dict, order_id: int
) -> dict[str, Any]:
    """Return packing sheet / label data for a supplier order."""
    user_id = get_user_id(current_user)
    supplier = _require_supplier_profile(db, user_id)
    order = _require_supplier_order(db, order_id, supplier.id)

    items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.supplier_id == supplier.id,
        )
        .all()
    )

    subtotal = float(sum((item.price or 0) * item.quantity for item in items))
    vat = float(order.tax_amount or 0)
    shipping = float(order.shipping_fee or 0)
    discount = float(order.discount_amount or 0)
    total = subtotal + vat + shipping - discount

    # Resolve shipment info if available
    shipment_info = resolve_shipment_info(db, order_id, supplier.id)

    return {
        "order_id": order.id,
        "order_number": order.order_number or f"ORD-{order.id}",
        "invoice_number": order.order_number or f"INV-{order.id}",
        "order_status": order.status,
        "payment_method": order.payment_method,
        "scan_code": f"ZOZI-{order.id}-{supplier.id}",
        "ordered_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
        "customer_name": getattr(order, "customer_name", get_user_attr(current_user, "username", "Customer") or "Customer"),
        "customer_email": getattr(order, "customer_email", ""),
        "customer_phone": getattr(order, "customer_phone", ""),
        "shipping_address": getattr(order, "shipping_address", None),
        "delivery_location": getattr(order, "delivery_location", None),
        "delivery_note": getattr(order, "delivery_note", None),
        "supplier_name": supplier.business_name or get_user_attr(current_user, "username", "Supplier"),
        "supplier_email": get_user_attr(current_user, "email", ""),
        "supplier_phone": getattr(supplier, "phone_business", None),
        "supplier_address": getattr(supplier, "address", None),
        "supplier_website": getattr(supplier, "website", None),
        "supplier_tax_id": getattr(supplier, "tax_id", None),
        "supplier_logo_url": getattr(supplier, "logo_url", None),
        "subtotal": subtotal,
        "vat": vat,
        "shipping": shipping,
        "discount": discount,
        "total": total,
        "currency": getattr(order, "currency", "OMR"),
        "has_shipment": shipment_info.get("has_shipment", False),
        "shipment_id": shipment_info.get("shipment_id"),
        "shipment_status": shipment_info.get("shipment_status", "pending"),
        "shipment_status_label": shipment_info.get("shipment_status_label", "Pending"),
        "tracking_number": shipment_info.get("tracking_number"),
        "carrier_name": shipment_info.get("carrier_name"),
        "current_hub": shipment_info.get("current_hub"),
        "package_count": shipment_info.get("package_count"),
        "package_weight_kg": shipment_info.get("package_weight_kg"),
        "package_dimensions": shipment_info.get("package_dimensions"),
        "packaging_notes": shipment_info.get("packaging_notes"),
        "packaged_at": shipment_info.get("packaged_at"),
        "items": [
            {
                "order_item_id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.price or 0),
                "line_total": float((item.price or 0) * item.quantity),
            }
            for item in items
        ],
    }


def get_supplier_order_for_user(
    db: Session, current_user: User | dict, order_id: int
) -> tuple[SupplierProfile, Order]:
    """Return ``(supplier_profile, order)`` for an order owned by this supplier.

    Raises 404 if the supplier profile is missing or the order does not include
    any item sold by this supplier.
    """
    user_id = get_user_id(current_user)
    supplier = _require_supplier_profile(db, user_id)
    order = _require_supplier_order(db, order_id, supplier.id)
    return supplier, order


def mark_order_prepared_if_processing(db: Session, order: Order) -> bool:
    """Move an order from ``processing`` to ``prepared``. Returns True if changed."""
    if order.status == "processing":
        order.status = "prepared"
        commit_only(db)
        return True
    return False


def get_order_for_parcel_verification(
    db: Session, current_user: User | dict, order_id: int
) -> Order:
    """Return the order to verify, checking supplier ownership via the product join."""
    user_id = get_user_id(current_user)
    _require_supplier_profile(db, user_id)

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

    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this supplier")

    return order


def get_parcel_item_descriptions(
    db: Session, current_user: User | dict, order_id: int
) -> list[str]:
    """Return ``"<product name> x<qty>"`` strings for the packing-sheet comparison."""
    user_id = get_user_id(current_user)
    items = (
        db.query(OrderItem)
        .join(OrderItem.product)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.product.has(supplier_id=user_id),
        )
        .all()
    )
    return [f"{item.product_name} x{item.quantity}" for item in items]


def list_supplier_order_ids(db: Session, current_user: User | dict) -> list[int]:
    """Return the distinct order IDs that contain items sold by this supplier."""
    user_id = get_user_id(current_user)
    supplier = _require_supplier_profile(db, user_id)
    return [
        row[0] for row in db.query(Order.id)
        .join(OrderItem)
        .filter(OrderItem.supplier_id == supplier.id)
        .distinct()
        .all()
    ]
