"""Public API exports for logistics domain — cross-domain service functions.

This module provides eager imports of logistics service functions needed by other domains.
It uses lazy imports internally to avoid circular dependencies.
"""
from __future__ import annotations

import importlib
from typing import Any

# Lazy import cache
_lazy_cache: dict[str, Any] = {}

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "get_partner_profile": ("domains.logistics.services.partners.logistics_partner_service", "get_partner_profile"),
    "update_partner_profile": ("domains.logistics.services.partners.logistics_partner_service", "update_partner_profile"),
    "review_logistics_partner_service_area": ("domains.logistics.services.partners.service", "review_logistics_partner_service_area"),
    "create_logistics_partner_service_area": ("domains.logistics.services.partners.service", "create_logistics_partner_service_area"),
    "update_logistics_partner_service_area": ("domains.logistics.services.partners.service", "update_logistics_partner_service_area"),
    "delete_logistics_partner_service_area": ("domains.logistics.services.partners.service", "delete_logistics_partner_service_area"),
    "normalize_country_code": ("domains.logistics.services.partners.service", "normalize_country_code"),
    "quote_shipping_for_destination": ("domains.logistics.services.partners.service", "quote_shipping_for_destination"),
    "normalize_city_name": ("domains.logistics.services.partners.service", "normalize_city_name"),
    "partner_can_service_order": ("domains.logistics.services.partners.service", "partner_can_service_order"),
    "partner_is_profile_approved": ("domains.logistics.services.partners.service", "partner_is_profile_approved"),
    "serialize_category_pricing_rule": ("domains.logistics.services.partners.service", "serialize_category_pricing_rule"),
    "serialize_pricing_profile": ("domains.logistics.services.partners.service", "serialize_pricing_profile"),
    "serialize_service_area": ("domains.logistics.services.partners.service", "serialize_service_area"),
    "serialize_vehicle_rule": ("domains.logistics.services.partners.service", "serialize_vehicle_rule"),
    "approve_partner": ("domains.logistics.services.core.admin_logistics_service", "approve_partner"),
    "list_partners": ("domains.logistics.services.core.admin_logistics_service", "list_partners"),
    "reject_partner": ("domains.logistics.services.core.admin_logistics_service", "reject_partner"),
    "toggle_partner_active": ("domains.logistics.services.core.admin_logistics_service", "toggle_partner_active"),
}


def __getattr__(name: str) -> Any:
    if name in _lazy_cache:
        return _lazy_cache[name]
    if name in _LAZY_EXPORTS:
        module_path, symbol = _LAZY_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, symbol)
        _lazy_cache[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return list(_LAZY_EXPORTS.keys()) + list(_lazy_cache.keys())