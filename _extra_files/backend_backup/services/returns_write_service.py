"""Backward-compatible re-export shim for return-request write operations.

This module intentionally performs NO imports at module-load time. The
canonical handlers live in `controllers.returns_controller`, which imports this
shim back; resolving names lazily via module-level `__getattr__` breaks that
import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_return_request": ("controllers.returns_controller", "create_return_request"),
    "update_return_request": ("controllers.returns_controller", "update_return_request"),
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
        raise NotImplementedError(f"'returns_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_return_notification = _missing_symbol("create_return_notification")
