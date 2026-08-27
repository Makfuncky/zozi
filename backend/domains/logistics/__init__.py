"""Logistics domain — public facade.

Exports the public API for the logistics domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "LogisticsService": ("domains.logistics.services.core.logistics_service", "LogisticsService"),
    "AdminLogisticsService": ("domains.logistics.services.core.admin_logistics_service", "AdminLogisticsService"),
    "AdminLogisticsFallbackService": ("domains.logistics.services.core.admin_logistics_fallback_service", "AdminLogisticsFallbackService"),
    "AdminLogisticsImportsService": ("domains.logistics.services.core.admin_logistics_imports_service", "AdminLogisticsImportsService"),
    "LogisticsHealthService": ("domains.logistics.services.health.logistics_health_service", "LogisticsHealthService"),
    "LogisticsLocationsService": ("domains.logistics.services.geo.logistics_locations_service", "LogisticsLocationsService"),
    "LogisticsGeographyService": ("domains.logistics.services.geo.admin_logistics_geography_service", "LogisticsGeographyService"),
    "LogisticsPartnerService": ("domains.logistics.services.partners.logistics_partner_service", "LogisticsPartnerService"),
    "ShipmentsService": ("domains.logistics.services.shipping.shipments_service", "ShipmentsService"),
    # models
    "Shipment": ("domains.logistics.models.logistics", "Shipment"),
    "LogisticsPartner": ("domains.logistics.models.logistics", "LogisticsPartner"),
    "LogisticsPartnerProfile": ("domains.logistics.models.logistics", "LogisticsPartnerProfile"),
    "ShippingCarrier": ("domains.logistics.models.logistics", "ShippingCarrier"),
    "ShippingZone": ("domains.logistics.models.logistics", "ShippingZone"),
    # ports
    "get_logistics_partner_by_id": ("domains.logistics.ports", "get_logistics_partner_by_id"),
    "list_logistics_partners": ("domains.logistics.ports", "list_logistics_partners"),
    "list_logistics_partners_page": ("domains.logistics.ports", "list_logistics_partners_page"),
    "get_shipment_by_id": ("domains.logistics.ports", "get_shipment_by_id"),
    "list_shipments": ("domains.logistics.ports", "list_shipments"),
    "list_shipments_page": ("domains.logistics.ports", "list_shipments_page"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.logistics' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
