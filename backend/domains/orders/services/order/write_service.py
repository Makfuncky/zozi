"""
Orders — Write Service (canonical).

Merged from:
  - domains/orders/services/order/orders_write_facade.py
  - domains/orders/services/order/orders_write_service.py

The sanctioned surface for order mutations. Providers (payments/*) must not
import domains.orders.models.orders directly — they call these functions
which return OrderDTO snapshots (never the ORM object).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.orders.models.orders import Order, OrderItem
from domains.orders.services.order_dtos import OrderDTO, OrderItemDTO, to_order_dto, to_order_item_dto
import structlog

logger = structlog.get_logger(__name__)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fetch(db: Session, order_id: int) -> Optional[Order]:
    return db.get(Order, order_id)


# ── ORM row writers (canonical home for order row-level writes) ────────────────

def create_order(db: Session, **order_data: Any) -> Order:
    """Insert a new order row (row writer — caller owns the transaction)."""
    order = Order(**order_data)
    db.add(order)
    db.flush()
    return order


def create_order_item(db: Session, **item_data: Any) -> OrderItem:
    """Insert a new order-item row (row writer — caller owns the transaction)."""
    item = OrderItem(**item_data)
    db.add(item)
    db.flush()
    return item


def update_order(db: Session, order: Order, updates: dict[str, Any]) -> Order:
    """Apply whitelisted column updates to an order and commit."""
    if updates:
        columns = {c.key for c in order.__table__.columns}
        for key, value in updates.items():
            if key in columns:
                setattr(order, key, value)
        if "updated_at" in columns:
            setattr(order, "updated_at", _utcnow())
    db.commit()
    return order


def _delete_order_rows(db: Session, order: Order) -> dict[str, int]:
    """Delete an order and its owned rows without committing."""
    order_id = order.id
    items = order.items
    shipments = order.shipments

    for item in items:
        db.delete(item)

    for shipment in shipments:
        for event in shipment.events:
            db.delete(event)
        db.delete(shipment)

    db.delete(order)
    db.flush()
    return {
        "order_id": order_id,
        "deleted_items": len(items or []),
        "deleted_shipments": len(shipments or []),
    }


def delete_order(db: Session, order: Order) -> dict[str, int]:
    """Delete an order; raises IntegrityError if related records block it."""
    info = _delete_order_rows(db, order)
    db.commit()
    return info


def delete_order_with_savepoint(db: Session, order: Order) -> dict[str, int] | None:
    """Delete one order inside a savepoint. Returns None if blocked by related records."""
    try:
        with db.begin_nested():
            info = _delete_order_rows(db, order)
        db.commit()
        return info
    except IntegrityError:
        db.rollback()
        return None


# ── Sanctioned mutation surface (DTO-based, for use by other domains) ───────────

def get_order_by_id(db: Session, order_id: int, include_items: bool = False) -> Optional[OrderDTO]:
    """Get order by ID as DTO snapshot."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(order, include_items=include_items)


def get_order_by_payment_intent_id(
    db: Session, payment_intent_id: str, include_items: bool = False
) -> Optional[OrderDTO]:
    """Get order by payment intent ID as DTO snapshot."""
    order = (
        db.query(Order)
        .filter(Order.payment_intent_id == str(payment_intent_id).strip())
        .first()
    )
    if order is None:
        return None
    return to_order_dto(order, include_items=include_items)


def get_order_by_order_number(
    db: Session, order_number: str, include_items: bool = False
) -> Optional[OrderDTO]:
    """Get order by order number as DTO snapshot."""
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        return None
    return to_order_dto(order, include_items=include_items)


def get_order_items(db: Session, order_id: int) -> List[OrderItemDTO]:
    """Get order items as DTO snapshots."""
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return [to_order_item_dto(i) for i in items]


def apply_order_status(db: Session, order_id: int, status: str) -> Optional[OrderDTO]:
    """Apply status change to an order. Returns updated DTO or None."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"status": status}))


def apply_order_payment_intent(
    db: Session, order_id: int, payment_intent_id: str
) -> Optional[OrderDTO]:
    """Apply payment intent ID to an order. Returns updated DTO or None."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(
        update_order(db, order, {"payment_intent_id": str(payment_intent_id).strip()})
    )


def apply_order_payment_method(
    db: Session, order_id: int, payment_method: str
) -> Optional[OrderDTO]:
    """Apply payment method to an order. Returns updated DTO or None."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"payment_method": payment_method}))


def mark_order_paid(
    db: Session, order_id: int, when: Optional[datetime] = None
) -> Optional[OrderDTO]:
    """Mark an order as paid. Returns updated DTO or None."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"paid_at": when or _now()}))


def apply_order_fields(db: Session, order_id: int, **fields) -> Optional[OrderDTO]:
    """Apply arbitrary whitelisted column updates to an order."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, fields))
