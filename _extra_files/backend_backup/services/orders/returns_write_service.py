"""Backward-compatible re-export shim for order return write operations.

The canonical implementations live in ``services.returns_write_service``.
Names are resolved lazily via module-level ``__getattr__`` so this shim never
contributes to an import-time cycle (the top-level shim re-exports the
``returns_controller`` back-reference).
"""
from __future__ import annotations

import importlib
from typing import Any

_SRC = "services.returns_write_service"

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_return_request": (_SRC, "create_return_request"),
    "update_return_request": (_SRC, "update_return_request"),
    "create_return_notification": (_SRC, "create_return_notification"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
