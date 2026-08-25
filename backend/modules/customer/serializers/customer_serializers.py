"""Customer module serializers (per-actor view models).

Per ARCHITECTURE_DIAGRAM.md §3, modules/{actor}/serializers/ holds
response shaping helpers that transform domain service output into
customer-facing API responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CustomerOrderSummary(BaseModel):
    """Customer-facing order summary."""
    id: int
    status: str
    total: float
    currency: str = "USD"
    created_at: Optional[datetime] = None
    items_count: int = 0


class CustomerProfileResponse(BaseModel):
    """Customer-facing profile response."""
    id: int
    email: str
    username: str
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None


class CartItemResponse(BaseModel):
    """Customer-facing cart item."""
    product_id: int
    quantity: int
    price: float
    name: str


def shape_order_for_customer(order: Dict[str, Any]) -> CustomerOrderSummary:
    """Shape a domain order dict into a customer-facing summary."""
    return CustomerOrderSummary(
        id=order.get("id", 0),
        status=order.get("status", "unknown"),
        total=float(order.get("total", 0)),
        currency=order.get("currency", "USD"),
        created_at=order.get("created_at"),
        items_count=len(order.get("items", [])),
    )


def shape_orders_for_customer(orders: List[Dict[str, Any]]) -> List[CustomerOrderSummary]:
    """Shape a list of domain orders into customer-facing summaries."""
    return [shape_order_for_customer(o) for o in orders]


__all__ = [
    "CustomerOrderSummary",
    "CustomerProfileResponse",
    "CartItemResponse",
    "shape_order_for_customer",
    "shape_orders_for_customer",
]
