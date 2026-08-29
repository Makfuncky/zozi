"""logistics domain — canonical model definitions.

This module is a pure re-export shim. The canonical table definitions live in
``domains.logistics.models.logistics_entities`` (production-grade columns: UUID,
version, soft-delete, audit, proper FKs). This shim keeps the 100+ existing
``from domains.logistics.models.logistics import X`` importers working without
re-registering any table on the shared MetaData.
"""
from __future__ import annotations

__all__ = [
    "LogisticsPartner",
    "LogisticsPartnerProfile",
    "LogisticsPartnerServiceArea",
    "LogisticsPricingProfile",
    "LogisticsVehicleRule",
    "LogisticsCategoryPricingRule",
    "Shipment",
    "ShipmentEvent",
]

from domains.logistics.models.logistics_entities import (  # noqa: F401
    LogisticsPartner,
    LogisticsPartnerProfile,
    LogisticsPartnerServiceArea,
    LogisticsPricingProfile,
    LogisticsVehicleRule,
    LogisticsCategoryPricingRule,
    Shipment,
    ShipmentEvent,
)


# Backwards-compatible re-export shims for models whose canonical home moved.
def __getattr__(name: str):
    _MAP = {
        "LogisticsPartnerLocation": ("domains.country.models.country_control", "LogisticsPartnerLocation"),
        "ParcelLocationTracker": ("domains.country.models.country_control", "ParcelLocationTracker"),
    }
    if name in _MAP:
        import importlib
        module_path, attr_name = _MAP[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
