"""Orders write-service façade — the sanctioned surface for order mutations.

This is the keystone for resolving ORD-CONSUMER (RESOLVER.md): it lets callers
that today do ``db.query(Order)`` + ``setattr(order, ...)`` + ``db.commit()``
inside ``providers/payments/*`` (Law 1 breach + ORM coupling) instead:

    dto = orders_write_facade.get_order_by_payment_intent_id(db, pi_id)
    ...
    orders_write_facade.apply_order_status(db, dto.id, "confirmed")

Reads return :class:`~domains.orders.services.order_dtos.OrderDTO` snapshots
(never the ORM object), and writes are keyed by ``order_id`` and applied through
the canonical row writer ``orders_write_service.update_order``. The façade lives
entirely inside the orders domain — it imports only orders models/services, so
it stays Law-1 clean (no ``providers.*`` / ``domains.*`` lateral imports).

Layer contract: each function owns its own transaction (``update_order`` commits).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from domains.orders.models.orders import Order, OrderItem
from domains.orders.services.core.dtos import OrderDTO, OrderItemDTO, to_order_dto, to_order_item_dto
from domains.orders.services.core.write_service import update_order


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fetch(db: Session, order_id: int) -> Optional[Order]:
    return db.get(Order, order_id)


def get_order_by_id(db: Session, order_id: int, include_items: bool = False) -> Optional[OrderDTO]:
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(order, include_items=include_items)


def get_order_by_payment_intent_id(
    db: Session, payment_intent_id: str, include_items: bool = False
) -> Optional[OrderDTO]:
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
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if order is None:
        return None
    return to_order_dto(order, include_items=include_items)


def get_order_items(db: Session, order_id: int) -> List[OrderItemDTO]:
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return [to_order_item_dto(i) for i in items]


def apply_order_status(db: Session, order_id: int, status: str) -> Optional[OrderDTO]:
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"status": status}))


def apply_order_payment_intent(
    db: Session, order_id: int, payment_intent_id: str
) -> Optional[OrderDTO]:
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(
        update_order(db, order, {"payment_intent_id": str(payment_intent_id).strip()})
    )


def apply_order_payment_method(
    db: Session, order_id: int, payment_method: str
) -> Optional[OrderDTO]:
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"payment_method": payment_method}))


def mark_order_paid(
    db: Session, order_id: int, when: Optional[datetime] = None
) -> Optional[OrderDTO]:
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, {"paid_at": when or _now()}))


def apply_order_fields(db: Session, order_id: int, **fields) -> Optional[OrderDTO]:
    """Apply an arbitrary whitelisted column update (used by later migrations)."""
    order = _fetch(db, order_id)
    if order is None:
        return None
    return to_order_dto(update_order(db, order, fields))
