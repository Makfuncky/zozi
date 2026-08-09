"""Backward-compatible re-export shim for commission write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.commission_controller`, which
created an import-time circular-import cycle (`commission_controller` ->
`commission_write_service` -> `commission_controller`). Resolving names lazily
via module-level `__getattr__` breaks that cycle: the underlying controller
module is only imported on first attribute access, by which point the importing
module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "delete_product_commission_override": (
        "controllers.commission_controller",
        "delete_product_commission_override",
    ),
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
        raise NotImplementedError(f"'commission_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_commission_agreement = _missing_symbol("create_commission_agreement")
create_product_commission_override = _missing_symbol("create_product_commission_override")
delete_commission_agreement = _missing_symbol("delete_commission_agreement")
update_commission_badge_tier = _missing_symbol("update_commission_badge_tier")
update_commission_category_rate = _missing_symbol("update_commission_category_rate")
update_commission_global_config = _missing_symbol("update_commission_global_config")
update_commission_ledger_entry = _missing_symbol("update_commission_ledger_entry")
update_product_commission_override = _missing_symbol("update_product_commission_override")
