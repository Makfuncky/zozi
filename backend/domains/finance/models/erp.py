"""ERP / finance domain models (schema ``finance``).

Logistics-related models (Warehouse, PurchaseOrder, GoodsReceiptNote, SalesOrder,
StockMovement, ImportShipment, and their line items) have been moved to
``domains.logistics.models.erp`` per ARCHITECTURE_DIAGRAM.md domain boundaries.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from infrastructure.database.types import GUID
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


# Backwards-compatible re-export shims. The logistics-owned ERP models
# (CustomsEntry, LandedCostAllocation, …) now live in
# ``domains.logistics.models.erp``. Importing them from here is kept working via
# a lazy ``__getattr__`` broker so existing call sites need not change.
_ERP_RE_EXPORTS: dict[str, tuple[str, str]] = {
    "CustomsEntry": ("domains.logistics.models.erp", "CustomsEntry"),
    "LandedCostAllocation": ("domains.logistics.models.erp", "LandedCostAllocation"),
    "ImportCostTemplate": ("domains.logistics.models.erp", "ImportCostTemplate"),
    "Warehouse": ("domains.logistics.models.erp", "Warehouse"),
    "PurchaseOrder": ("domains.logistics.models.erp", "PurchaseOrder"),
    "GoodsReceiptNote": ("domains.logistics.models.erp", "GoodsReceiptNote"),
    "SalesOrder": ("domains.logistics.models.erp", "SalesOrder"),
    "StockMovement": ("domains.logistics.models.erp", "StockMovement"),
    "ImportShipment": ("domains.logistics.models.erp", "ImportShipment"),
}


def __getattr__(name: str):
    if name in _ERP_RE_EXPORTS:
        import importlib
        module_path, attr_name = _ERP_RE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


