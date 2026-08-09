"""Backward-compatible re-export shim for logistics write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.logistics_controller`,
`routers.public_logistics_access` and `routers.public_shipments_access`, which created import-time
circular-import cycles (`logistics_controller` -> `logistics_write_service` ->
`logistics_controller`). Resolving names lazily via module-level `__getattr__`
breaks those cycles: the underlying modules are only imported on first
attribute access, by which point the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "delete_shipping_zone": ("controllers.logistics_controller", "delete_shipping_zone"),
    "update_shipping_zone": ("routers.public_logistics_access", "update_shipping_zone"),
    "update_shipment": ("routers.public_shipments_access", "update_shipment"),
    "add_and_flush": ("services.write_help", "add_and_flush"),
    "commit_only": ("services.write_help", "commit_only"),
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
        raise NotImplementedError(f"'logistics_write_service.{name}' is not implemented (refactor gap)")
    return _f


create_shipping_carrier = _missing_symbol("create_shipping_carrier")
create_shipping_zone = _missing_symbol("create_shipping_zone")
refresh_model = _missing_symbol("refresh_model")
update_shipment_event = _missing_symbol("update_shipment_event")
update_shipping_carrier = _missing_symbol("update_shipping_carrier")
