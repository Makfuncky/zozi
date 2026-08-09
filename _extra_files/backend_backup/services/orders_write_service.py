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

_REEXPORTS: dict[str, tuple[str, str]] = {
    # No surviving canonical implementations: the ORM-level order persistence
    # helpers were lost in the layered reorg. See the stubs below.
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# The following symbols were referenced but have NO definition anywhere in the
# codebase. They are stubbed to fail loudly at call time rather than break
# import of this module.
#
# NOTE: `create_order` here is the ORM row-writer (called as
# `create_order_model(db, **order_columns)`), NOT the orchestrating
# `controllers.orders_controller.create_order(order, current_user, db)`.
# Mapping it to the controller would recurse infinitely, so it is stubbed.
def _missing_symbol(name: str):
    def _f(*_a, **_k):
        raise NotImplementedError(f"'orders_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_order = _missing_symbol("create_order")
create_order_item = _missing_symbol("create_order_item")
update_order = _missing_symbol("update_order")
