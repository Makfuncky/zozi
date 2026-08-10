"""Orders write service — ORM-level row writers for order persistence.

This module is the canonical home for order row-level writes. It is referenced
by ``controllers.orders.orders`` (admin order operations) and the lazy
re-export shim ``services.orders_write_service``.

Layer contract: only ``services/`` owns DB transactions. Each function here
takes a caller-provided ``Session`` and owns only the narrow write it performs
(row insert / field update / ordered delete). Savepoint semantics for bulk
deletes live in ``delete_order_with_savepoint`` so a single blocked order does
not abort the whole batch.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Order, OrderItem


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    """Delete an order and its owned rows without committing.

    Flushes inside the caller's transaction (savepoint when bulk) so foreign-key
    violations surface as ``IntegrityError`` here rather than at commit time.
    """
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
    """Delete an order; raises ``IntegrityError`` if related records block it."""
    info = _delete_order_rows(db, order)
    db.commit()
    return info


def delete_order_with_savepoint(db: Session, order: Order) -> dict[str, int] | None:
    """Delete one order inside a savepoint.

    Returns the deletion summary on success, or ``None`` when the order still
    has related records that must be archived/removed first (the savepoint is
    rolled back so the rest of the batch is unaffected).
    """
    try:
        with db.begin_nested():
            info = _delete_order_rows(db, order)
        db.commit()
        return info
    except IntegrityError:
        db.rollback()
        return None
