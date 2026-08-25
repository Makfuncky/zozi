"""Supplier module serializers (per-actor view models).

Per ARCHITECTURE_DIAGRAM.md §3, modules/{actor}/serializers/ holds
response shaping helpers that transform domain service output into
supplier-facing API responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SupplierOrderSummary(BaseModel):
    """Supplier-facing order summary."""
    id: int
    status: str
    total: float
    currency: str = "USD"
    created_at: Optional[datetime] = None


class SupplierProfileResponse(BaseModel):
    """Supplier-facing profile response."""
    id: int
    name: str
    slug: str
    status: str
    country_code: Optional[str] = None
    rating: float = 0.0


class PayoutSummary(BaseModel):
    """Supplier-facing payout summary."""
    id: int
    amount: float
    currency: str = "USD"
    status: str
    period: Optional[str] = None
    created_at: Optional[datetime] = None


def shape_order_for_supplier(order: Dict[str, Any]) -> SupplierOrderSummary:
    """Shape a domain order dict into a supplier-facing summary."""
    return SupplierOrderSummary(
        id=order.get("id", 0),
        status=order.get("status", "unknown"),
        total=float(order.get("total", 0)),
        currency=order.get("currency", "USD"),
        created_at=order.get("created_at"),
    )


__all__ = [
    "SupplierOrderSummary",
    "SupplierProfileResponse",
    "PayoutSummary",
    "shape_order_for_supplier",
]
