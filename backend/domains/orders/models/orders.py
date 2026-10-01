"""Orders domain models — re-export shim.

Canonical definitions live in ``domains.orders.models.order_entities``.
This module re-exports them for backward compatibility.
"""
from __future__ import annotations

__all__ = ["Order", "OrderItem", "OrderLogisticsAllocation", "ReturnRequest"]

_CANONICAL_EXPORTS = {
    "Order": ("domains.orders.models.order_entities", "Order"),
    "OrderItem": ("domains.orders.models.order_entities", "OrderItem"),
    "OrderLogisticsAllocation": ("domains.orders.models.order_entities", "OrderLogisticsAllocation"),
    "ReturnRequest": ("domains.orders.models.order_entities", "ReturnRequest"),
}

_IMPORTED: dict[str, object] = {}


def __getattr__(name: str):
    """Lazy import of canonical models to avoid InvalidRequestError."""
    if name in _IMPORTED:
        return _IMPORTED[name]
    if name in _CANONICAL_EXPORTS:
        module_path, class_name = _CANONICAL_EXPORTS[name]
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        _IMPORTED[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
