"""Supplier module — public facade.

Exports the public API for the supplier module (routers, services, serializers).
Uses lazy imports to avoid circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # routers (only the 5 that actually exist)
    "accounts_router": ("modules.supplier.routers.accounts", "router"),
    "analytics_router": ("modules.supplier.routers.analytics", "router"),
    "catalog_router": ("modules.supplier.routers.catalog", "router"),
    "finance_router": ("modules.supplier.routers.finance", "router"),
    "orders_router": ("modules.supplier.routers.orders", "router"),
    "suppliers_router": ("modules.supplier.routers.suppliers", "router"),
    # auth
    "require_supplier": ("modules.supplier.auth.dependencies", "require_supplier"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'modules.supplier' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
