"""Orders domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Re-exports from services/events.py for public API consistency.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Event type constants
    "EVENT_ORDER_CREATED": ("domains.orders.services.events", "EVENT_ORDER_CREATED"),
    "EVENT_ORDER_CONFIRMED": ("domains.orders.services.events", "EVENT_ORDER_CONFIRMED"),
    "EVENT_ORDER_SHIPPED": ("domains.orders.services.events", "EVENT_ORDER_SHIPPED"),
    "EVENT_ORDER_DELIVERED": ("domains.orders.services.events", "EVENT_ORDER_DELIVERED"),
    "EVENT_ORDER_CANCELLED": ("domains.orders.services.events", "EVENT_ORDER_CANCELLED"),
    # Event classes
    "OrdersEvent": ("domains.orders.services.events", "OrdersEvent"),
    "OrderCreated": ("domains.orders.services.events", "OrderCreated"),
    "OrderConfirmed": ("domains.orders.services.events", "OrderConfirmed"),
    "OrderShipped": ("domains.orders.services.events", "OrderShipped"),
    "OrderDelivered": ("domains.orders.services.events", "OrderDelivered"),
    "OrderCancelled": ("domains.orders.services.events", "OrderCancelled"),
    # Publish helpers
    "publish_order_created": ("domains.orders.services.events", "publish_order_created"),
    "publish_order_confirmed": ("domains.orders.services.events", "publish_order_confirmed"),
    "publish_order_shipped": ("domains.orders.services.events", "publish_order_shipped"),
    "publish_order_delivered": ("domains.orders.services.events", "publish_order_delivered"),
    "publish_order_cancelled": ("domains.orders.services.events", "publish_order_cancelled"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.orders.events' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
