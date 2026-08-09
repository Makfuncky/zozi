"""Backward-compatible re-export shim for order write operations.

This module intentionally performs NO imports at module-load time so that it
can be imported from `controllers.orders_controller` /
`controllers.admin.orders` without creating an import-time circular-import
cycle. Names are resolved lazily via module-level `__getattr__`, so the
underlying module is only imported on first attribute access, by which point
the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any
import structlog
logger = structlog.get_logger(__name__)

_REEXPORTS: dict[str, tuple[str, str]] = {
    # ORM-level order persistence helpers live in the canonical
    # `services.orders.orders_write_service` module. These are the row-writers
    # (e.g. `create_order(db, **order_data)`), NOT the orchestrating
    # `controllers.orders_controller.create_order`. Resolved lazily to avoid an
    # import-time cycle with `controllers.orders_controller` /
    # `controllers.admin.orders`.
    "create_order": ("services.orders.orders_write_service", "create_order"),
    "create_order_item": ("services.orders.orders_write_service", "create_order_item"),
    "update_order": ("services.orders.orders_write_service", "update_order"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
