"""Order DTOs — ORM-free snapshots passed across the orders domain boundary.

Providers (``providers/payments/*``) currently import ``domains.orders.models.orders``
and mutate the ORM ``Order`` directly (Law 1 breach + ORM coupling, see
RESOLVER.md ORD-CONSUMER). The migration path is: the calling domain service
queries the real ``Order`` inside the orders domain, hands the provider a
:class:`OrderDTO` snapshot, and applies the provider's result back through
``orders_write_facade``. DTOs are plain dataclasses so they never pull the ORM
session graph across the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class OrderItemDTO:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None
    country_code: Optional[str] = None


@dataclass
class OrderDTO:
    id: int
    order_number: Optional[str] = None
    user_id: Optional[int] = None
    customer_id: Optional[int] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_provider: Optional[str] = None
    payment_intent_id: Optional[str] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None
    country_code: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    items: list[OrderItemDTO] = field(default_factory=list)


def to_order_item_dto(orm_item) -> OrderItemDTO:
    return OrderItemDTO(
        id=orm_item.id,
        order_id=orm_item.order_id,
        product_id=orm_item.product_id,
        quantity=orm_item.quantity,
        unit_price=orm_item.unit_price,
        price=orm_item.price,
        total_price=orm_item.total_price,
        selected_size=orm_item.selected_size,
        selected_color=orm_item.selected_color,
        country_code=orm_item.country_code,
    )


def to_order_dto(orm_order, include_items: bool = False) -> OrderDTO:
    """Build an :class:`OrderDTO` from an ORM ``Order`` (scalar columns only)."""
    dto = OrderDTO(
        id=orm_order.id,
        order_number=orm_order.order_number,
        user_id=orm_order.user_id,
        customer_id=orm_order.customer_id,
        status=orm_order.status,
        payment_status=orm_order.payment_status,
        payment_method=orm_order.payment_method,
        payment_provider=orm_order.payment_provider,
        payment_intent_id=orm_order.payment_intent_id,
        total=orm_order.total,
        currency=orm_order.currency,
        country_code=orm_order.country_code,
        paid_at=orm_order.paid_at,
        created_at=orm_order.created_at,
    )
    if include_items and orm_order.items:
        dto.items = [to_order_item_dto(i) for i in orm_order.items]
    return dto
