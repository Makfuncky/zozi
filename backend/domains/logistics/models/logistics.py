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

