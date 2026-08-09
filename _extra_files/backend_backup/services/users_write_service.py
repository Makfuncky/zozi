"""Backward-compatible re-export shim for admin user write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.admin.users`, which created an
import-time circular-import cycle (`controllers.admin.users` ->
`users_write_service` -> `controllers.admin.users`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "delete_bank_account_record": ("controllers.admin.users", "delete_bank_account_record"),
    "toggle_user_active": ("controllers.admin.users", "toggle_user_active"),
    "update_user_role": ("controllers.admin.users", "update_user_role"),
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
        raise NotImplementedError(f"'users_write_service.{name}' is not implemented (refactor gap)")
    return _f


_build_user_delete_blocker = _missing_symbol("_build_user_delete_blocker")
_delete_order_records = _missing_symbol("_delete_order_records")
_hard_delete_user_record = _missing_symbol("_hard_delete_user_record")
create_chatbot_query_event = _missing_symbol("create_chatbot_query_event")
create_staff_user = _missing_symbol("create_staff_user")
force_reset_password = _missing_symbol("force_reset_password")
update_bank_account_verification = _missing_symbol("update_bank_account_verification")
update_staff_user = _missing_symbol("update_staff_user")
update_user_browsing_history = _missing_symbol("update_user_browsing_history")
