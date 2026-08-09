"""Backward-compatible re-export shim for cart write operations.

The canonical implementations live in `services.orders.cart_write_service`.
Names are resolved lazily via module-level `__getattr__` so this shim never
contributes to an import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_SRC = "services.orders.cart_write_service"

_REEXPORTS: dict[str, tuple[str, str]] = {
    "commit_cart_items": (_SRC, "commit_cart_items"),
    "create_cart_item": (_SRC, "create_cart_item"),
    "delete_cart_item": (_SRC, "delete_cart_item"),
    "delete_cart_items_by_user": (_SRC, "delete_cart_items_by_user"),
    "update_cart_item": (_SRC, "update_cart_item"),
    "load_cart_items": (_SRC, "load_cart_items"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
