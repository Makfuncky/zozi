"""Generated re-export shim (lazy).

Re-exports symbols from their canonical locations via PEP 562
__getattr__ so importing this module never triggers the load-time
controller/router imports that caused circular imports. Legacy
`from services.products_write_service import ...` keeps working;
the target module is imported only when the symbol is first accessed
(which happens at call time, after all modules are loaded)."""
from __future__ import annotations

import importlib
from typing import Callable

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_flash_sale": ("controllers.flash_sale_controller", "create_flash_sale"),
    "delete_flash_sale": ("controllers.flash_sale_controller", "delete_flash_sale"),
    "update_flash_sale": ("controllers.flash_sale_controller", "update_flash_sale"),
    "create_product": ("controllers.products_controller", "create_product"),
    "update_product": ("controllers.products_controller", "update_product"),
    "reorder_categories": ("routers.admin_categories_governance", "reorder_categories"),
    "create_category": ("services.permission_service", "create_category"),
    "delete_category": ("services.permission_service", "delete_category"),
    "update_category": ("services.permission_service", "update_category")
}

_MISSING: frozenset[str] = frozenset({
    "archive_product_reviews",
    "clear_product_carts",
    "clear_product_wishlists",
    "create_product_verification",
    "update_product_rating",
    "update_product_verification"
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
