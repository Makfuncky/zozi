"""Backward-compatible re-export shim for role-permission write operations.

Names are resolved lazily via module-level `__getattr__` so this shim never
contributes to an import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    # No surviving canonical implementation. See the stub below.
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
        raise NotImplementedError(f"'permissions_write_service.{name}' is not implemented (refactor gap)")
    return _f


upsert_role_permission_setting = _missing_symbol("upsert_role_permission_setting")
