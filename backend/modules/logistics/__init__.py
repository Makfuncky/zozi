"""Logistics module — public facade.

Exports the public API for the logistics module (routers, services, serializers).
Uses lazy imports to avoid circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # routers (only the 1 that actually exists)
    "logistics_router": ("modules.logistics.routers.logistics", "router"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'modules.logistics' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
