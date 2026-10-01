"""Country domain — public facade.

Exports the public API for the country domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "CountryService": ("domains.country.services.core.country_service", "CountryService"),
    "CountryConfigAdminService": ("domains.country.services.core.country_config_admin_service", "CountryConfigAdminService"),
    "CountryContextService": ("domains.country.services.core.country_context_service", "CountryContextService"),
    "CrossBorderService": ("domains.country.services.cross_border.cross_border_service", "CrossBorderService"),
    "LocalizationService": ("domains.country.services.localization.localization_service", "LocalizationService"),
    "TranslationService": ("domains.country.services.localization.translation_service", "TranslationService"),
    "CountryDetection": ("domains.country.services.geo.country_detection", "CountryDetection"),
    "CountryMapsService": ("domains.country.services.geo.country_maps_service", "CountryMapsService"),
    "CountryTaxService": ("domains.country.services.tax.country_tax_service", "CountryTaxService"),
    "CountryRestrictionService": ("domains.country.services.restriction.country_restriction_service", "CountryRestrictionService"),
    # models
    "Country": ("domains.country.models.countries", "Country"),
    "CountryControl": ("domains.country.models.country_control", "CountryControl"),
    "CountryBasics": ("domains.country.models.country_basics", "CountryBasics"),
    # functions
    "get_country_or_404": ("infrastructure.utils.country_rls", "get_country_or_404"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.country' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
