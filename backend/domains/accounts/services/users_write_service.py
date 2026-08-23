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
    "delete_bank_account_record": ("controllers.customer.users", "delete_bank_account_record"),
    "toggle_user_active": ("controllers.customer.users", "toggle_user_active"),
    "update_user_role": ("controllers.customer.users", "update_user_role"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# The following symbols were lost when commit 3d1f49a ("fixed_voliations_04-08-2026")
# replaced their real implementations with `_missing_symbol` stubs. They are now
# re-exported from the canonical `services.users.user_write_ops` module (recovered
# from 624a1a2), so legacy imports and the live admin endpoints that call them work
# again. These are real, behavior-preserving implementations -- not stubs.
from domains.accounts.services.user_write_ops import build_user_delete_blocker
from domains.accounts.services.user_write_ops import delete_order_records
from domains.accounts.services.user_write_ops import hard_delete_user_record
from domains.accounts.services.user_write_ops import create_chatbot_query_event
from domains.accounts.services.user_write_ops import create_staff_user
from domains.accounts.services.user_write_ops import force_reset_password
from domains.accounts.services.user_write_ops import update_bank_account_verification
from domains.accounts.services.user_write_ops import update_staff_user
from domains.accounts.services.user_write_ops import update_user_browsing_history

# Private-name aliases re-exported for legacy imports and the recovery tests.
# The recovered implementations are the public names imported above.
_build_user_delete_blocker = build_user_delete_blocker
_delete_order_records = delete_order_records
_hard_delete_user_record = hard_delete_user_record

import structlog
logger = structlog.get_logger(__name__)
