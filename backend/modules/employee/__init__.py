"""Employee module — public facade.

Exports the public API for the employee module (routers, services, serializers).
Uses lazy imports to avoid circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # routers (only the 8 that actually exist)
    "accounts_router": ("modules.employee.routers.accounts", "router"),
    "comms_router": ("modules.employee.routers.comms", "router"),
    "country_router": ("modules.employee.routers.country", "router"),
    "finance_router": ("modules.employee.routers.finance", "router"),
    "expense_router": ("modules.employee.routers.finance", "expense_router"),
    "hr_router": ("modules.employee.routers.hr", "router"),
    "orders_router": ("modules.employee.routers.orders", "router"),
    "security_router": ("modules.employee.routers.security", "router"),
    "suppliers_router": ("modules.employee.routers.suppliers", "router"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'modules.employee' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
