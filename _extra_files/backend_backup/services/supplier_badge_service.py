"""Backward-compatible re-export shim for supplier badge/credibility operations.

This module intentionally performs NO imports at module-load time so it can be
imported from `controllers.supplier_controller`, `controllers.supplier.badge`
and `services.cash_management_service` without creating an import-time
circular-import cycle. Names are resolved lazily via module-level
`__getattr__`.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    # No surviving canonical implementations: the supplier badge service body
    # was lost in the layered reorg. See the stubs below.
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
        raise NotImplementedError(f"'supplier_badge_service.{name}' is not implemented (refactor gap)")
    return _f


admin_set_supplier_badge = _missing_symbol("admin_set_supplier_badge")
compute_credibility_score = _missing_symbol("compute_credibility_score")
list_supplier_badge_billing_history = _missing_symbol("list_supplier_badge_billing_history")
list_supplier_badge_catalog = _missing_symbol("list_supplier_badge_catalog")
purchase_supplier_badge = _missing_symbol("purchase_supplier_badge")
record_badge_billing_payment = _missing_symbol("record_badge_billing_payment")
refresh_supplier_badge = _missing_symbol("refresh_supplier_badge")
run_badge_recalculation_cycle = _missing_symbol("run_badge_recalculation_cycle")
