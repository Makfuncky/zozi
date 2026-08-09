"""Generated re-export shim (lazy).

Re-exports symbols from their canonical locations via PEP 562
__getattr__ so importing this module never triggers the load-time
controller/router imports that caused circular imports."""
from __future__ import annotations

import importlib
from typing import Callable

_REEXPORTS: dict[str, tuple[str, str]] = {
    "clear_wishlist": ("controllers.commerce.package", "clear_wishlist"),
    "create_review": ("controllers.reviews_controller", "create_review"),
    "update_review": ("controllers.reviews_controller", "update_review"),
    "delete_review": ("controllers.reviews_controller", "delete_review"),
    "create_address": ("services.commerce.customer_router_service", "create_address"),
    "delete_address": ("services.commerce.customer_router_service", "delete_address"),
    "set_default_address": ("services.commerce.customer_router_service", "set_default_address"),
    "update_address": ("services.commerce.customer_router_service", "update_address")
}

_MISSING: frozenset[str] = frozenset({
    "create_wishlist_item",
    "delete_wishlist_item",
    "soft_delete_review",
    "unset_other_default_addresses"
})

def _make_missing(name: str) -> Callable:
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'{__name__}.{name}' is not implemented (refactor gap)")
    _f.__name__ = name
    return _f

def __getattr__(name: str):
    spec = _REEXPORTS.get(name)
    if spec is not None:
        module = importlib.import_module(spec[0])
        value = getattr(module, spec[1])
        globals()[name] = value
        return value
    if name in _MISSING:
        value = _make_missing(name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(set(globals()) | set(_REEXPORTS) | set(_MISSING))
