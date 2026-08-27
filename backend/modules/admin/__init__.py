"""Admin module — public facade.

Exports the public API for the admin module (routers, services, serializers).
Uses lazy imports to avoid circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # routers
    "accounts_router": ("modules.admin.routers.accounts", "router"),
    "analytics_router": ("modules.admin.routers.analytics", "router"),
    "audit_router": ("modules.admin.routers.audit", "router"),
    "catalog_router": ("modules.admin.routers.catalog", "router"),
    "comms_router": ("modules.admin.routers.comms", "router"),
    "country_router": ("modules.admin.routers.country", "router"),
    "customers_router": ("modules.admin.routers.customers", "router"),
    "finance_router": ("modules.admin.routers.finance", "router"),
    "governance_router": ("modules.admin.routers.governance", "router"),
    "hr_router": ("modules.admin.routers.hr", "router"),
    "logistics_router": ("modules.admin.routers.logistics", "router"),
    "orders_router": ("modules.admin.routers.orders", "router"),
    "promotions_router": ("modules.admin.routers.promotions", "router"),
    "security_router": ("modules.admin.routers.security", "router"),
    "suppliers_router": ("modules.admin.routers.suppliers", "router"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'modules.admin' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
