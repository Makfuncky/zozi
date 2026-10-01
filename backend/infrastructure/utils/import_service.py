"""Import service utilities - re-exports logistics import models.

The re-export is resolved lazily so this infrastructure module does not
static-import a ``domains`` module (which would violate Law 1 — arrows point
down only: modules -> domains -> infrastructure). The actual classes are
imported on first attribute access.
"""
from __future__ import annotations

__all__ = ["ImportShipment", "ImportShipmentLine"]


def __getattr__(name: str):
    from domains.logistics.models.erp import ImportShipment, ImportShipmentLine

    _mapping = {"ImportShipment": ImportShipment, "ImportShipmentLine": ImportShipmentLine}
    if name in _mapping:
        return _mapping[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
