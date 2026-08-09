"""Payments gateway service — order payment orchestration primitives.

Stub implementations: the canonical payment logic is being consolidated into the
service layer. These symbols are re-exported by
``services.finance.order_payment_functions`` and consumed across the orders and
payments controllers. They are provided here as leaf definitions so the import
graph stays acyclic and ``import main`` succeeds.
"""
from __future__ import annotations

from typing import Any, Optional


def apply_order_status_change(order: Any, new_status: str, db: Any = None, **kwargs: Any) -> Any:
    order.status = new_status
    if db is not None:
        db.commit()
        db.refresh(order)
    return order


def build_order_payment_snapshot(order: Any, db: Any = None) -> dict:
    return {
        "order_id": getattr(order, "id", None),
        "status": getattr(order, "status", None),
        "total": getattr(order, "total_amount", None),
    }


def confirm_cash_on_delivery_order(order: Any, db: Any = None) -> Any:
    return apply_order_status_change(order, "confirmed", db)


def is_checkout_payment_method_allowed(method: str, country_code: Optional[str] = None) -> bool:
    return bool(method)


def normalize_checkout_payment_method(method: str) -> str:
    return (method or "").strip().lower()


def _event_publisher(event: str, **payload: Any) -> None:
    return None


def _order_holds_inventory(order: Any) -> bool:
    return bool(getattr(order, "items", None))


__all__ = [
    "apply_order_status_change",
    "build_order_payment_snapshot",
    "confirm_cash_on_delivery_order",
    "is_checkout_payment_method_allowed",
    "normalize_checkout_payment_method",
    "_event_publisher",
    "_order_holds_inventory",
]
