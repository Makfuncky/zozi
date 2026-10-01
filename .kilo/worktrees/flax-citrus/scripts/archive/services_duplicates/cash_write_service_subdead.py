"""Backward-compatible re-export shim for treasury cash write operations.

The canonical implementations live in `services.treasury.cash_write_service`.
Names are resolved lazily via module-level `__getattr__` so this shim never
contributes to an import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any
import structlog
logger = structlog.get_logger(__name__)

_SRC = "services.treasury.cash_write_service"

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_cash_account": (_SRC, "create_cash_account"),
    "create_cash_transaction": (_SRC, "create_cash_transaction"),
    "get_cash_account": (_SRC, "get_cash_account"),
    "list_cash_accounts": (_SRC, "list_cash_accounts"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
