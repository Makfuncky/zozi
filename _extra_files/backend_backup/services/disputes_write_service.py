"""Backward-compatible re-export shim for supplier dispute write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.disputes_controller`, which
created an import-time circular-import cycle (`disputes_controller` ->
`disputes_write_service` -> `disputes_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_supplier_dispute": ("controllers.disputes_controller", "create_supplier_dispute"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# The following symbols were referenced but have NO definition anywhere in the
# codebase. They are stubbed to fail loudly at call time rather than break
# import of this module.
def _missing_symbol(name: str):
    def _f(*_a, **_k):
        raise NotImplementedError(f"'disputes_write_service.{name}' is not implemented (refactor gap)")
    return _f


bulk_update_disputes = _missing_symbol("bulk_update_disputes")
create_dispute_notification = _missing_symbol("create_dispute_notification")
create_dispute_notification_for_update = _missing_symbol("create_dispute_notification_for_update")
create_supplier_notification_preference = _missing_symbol("create_supplier_notification_preference")
update_supplier_dispute = _missing_symbol("update_supplier_dispute")
update_supplier_notification_preference = _missing_symbol("update_supplier_notification_preference")
