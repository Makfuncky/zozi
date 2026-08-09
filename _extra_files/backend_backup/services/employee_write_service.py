"""Backward-compatible re-export shim for employee write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.employees_controller`, which
created an import-time circular-import cycle (`employees_controller` ->
`employee_write_service` -> `employees_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "approve_work_log": ("controllers.employees_controller", "approve_work_log"),
    "create_employee": ("controllers.employees_controller", "create_employee"),
    "create_employee_document": ("controllers.employees_controller", "create_employee_document"),
    "create_employee_relation": ("controllers.employees_controller", "create_employee_relation"),
    "create_employee_role": ("controllers.employees_controller", "create_employee_role"),
    "create_leave_request": ("controllers.employees_controller", "create_leave_request"),
    "create_office": ("controllers.employees_controller", "create_office"),
    "delete_employee": ("controllers.employees_controller", "delete_employee"),
    "delete_office": ("controllers.employees_controller", "delete_office"),
    "update_employee": ("controllers.employees_controller", "update_employee"),
    "update_office": ("controllers.employees_controller", "update_office"),
    "create_shift_roster": ("services.shift_roster_service", "create_shift_roster"),
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
        raise NotImplementedError(f"'employee_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_dynamic_qr_session = _missing_symbol("create_dynamic_qr_session")
create_employee_attendance = _missing_symbol("create_employee_attendance")
create_employee_work_log = _missing_symbol("create_employee_work_log")
create_revoked_token = _missing_symbol("create_revoked_token")
delete_employee_relation = _missing_symbol("delete_employee_relation")
update_dynamic_qr_session = _missing_symbol("update_dynamic_qr_session")
update_employee_attendance = _missing_symbol("update_employee_attendance")
update_employee_document = _missing_symbol("update_employee_document")
update_qr_sessions_expiry = _missing_symbol("update_qr_sessions_expiry")
