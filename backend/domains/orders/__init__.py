"""Orders domain — public facade.

Exports the public API for the orders domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "OrdersService": ("domains.orders.services.orders_service", "OrdersService"),
    "AdminOrdersService": ("domains.orders.services.admin_orders_service", "AdminOrdersService"),
    "AdminOrdersStatusService": ("domains.orders.services.admin_orders_status_service", "AdminOrdersStatusService"),
    "AdminCatalogOrdersService": ("domains.orders.services.admin_catalog_orders_service", "AdminCatalogOrdersService"),
    "OrdersPackageService": ("domains.orders.services.orders_package_service", "OrdersPackageService"),
    "OrderEngine": ("domains.orders.services.core.order_engine", "OrderEngine"),
    "CartService": ("domains.orders.services.cart.service", "CartService"),
    "CheckoutService": ("domains.orders.services.checkout.service", "CheckoutService"),
    # models
    "Order": ("domains.orders.models.orders", "Order"),
    "OrderEntity": ("domains.orders.models.order_entities", "OrderEntity"),
    # functions
    "create_order": ("domains.orders.services.core.service", "create_order"),
    "get_order_by_id": ("domains.orders.services.orders_service", "get_order_by_id"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.orders' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
