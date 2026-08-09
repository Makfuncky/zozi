"""Backward-compatible re-export shim for banner write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.banner_controller`, which created
an import-time circular-import cycle (`banner_controller` ->
`banner_write_service` -> `banner_controller`). Resolving names lazily via
module-level `__getattr__` breaks that cycle: the underlying controller module
is only imported on first attribute access, by which point the importing module
is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_banner": ("controllers.banner_controller", "create_banner"),
    "delete_banner": ("controllers.banner_controller", "delete_banner"),
    "reorder_banners": ("controllers.banner_controller", "reorder_banners"),
    "update_banner": ("controllers.banner_controller", "update_banner"),
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
        raise NotImplementedError(f"'banner_write_service.{name}' is not implemented (refactor gap)")
    return _f


add_banner_if_missing = _missing_symbol("add_banner_if_missing")
bulk_add_banners = _missing_symbol("bulk_add_banners")
update_banner_image = _missing_symbol("update_banner_image")
