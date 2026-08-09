"""Backward-compatible re-export shim for HR write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.hr_controller`, which created an
import-time circular-import cycle (`hr_controller` -> `hr_write_service` ->
`hr_controller`). Resolving names lazily via module-level `__getattr__` breaks
that cycle: the underlying controller module is only imported on first
attribute access, by which point the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_coi_report": ("controllers.hr_controller", "create_coi_report"),
    "create_disciplinary_case": ("controllers.hr_controller", "create_disciplinary_case"),
    "create_offboarding_case": ("controllers.hr_controller", "create_offboarding_case"),
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
        raise NotImplementedError(f"'hr_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_employee_address = _missing_symbol("create_employee_address")
create_employee_dependent = _missing_symbol("create_employee_dependent")
upsert_employee_risk_score = _missing_symbol("upsert_employee_risk_score")
