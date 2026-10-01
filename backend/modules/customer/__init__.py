"""Customer module — public facade.

Exports the public API for the customer module (routers, services, serializers).
Uses lazy imports to avoid circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # routers (only the 6 that actually exist)
    "accounts_router": ("modules.customer.routers.accounts", "router"),
    "comms_router": ("modules.customer.routers.comms", "router"),
    "customers_router": ("modules.customer.routers.customers", "router"),
    "finance_router": ("modules.customer.routers.finance", "router"),
    "orders_router": ("modules.customer.routers.orders", "router"),
    "promotions_router": ("modules.customer.routers.promotions", "router"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'modules.customer' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
