"""Lazy domain model registry for seed scripts.

Seed scripts require direct model access to populate the database.
To comply with Law 1 (infrastructure must not import domains), all
domain models are resolved lazily at call time, not at import time.
"""
from __future__ import annotations

import importlib as _importlib

# Registry: model_name → (module_path, class_name)
_REGISTRY: dict[str, tuple[str, str]] = {
    # accounts
    "User": ("domains.accounts.models.user", "User"),
    # catalog
    "Category": ("domains.catalog.models.products", "Category"),
    "Product": ("domains.catalog.models.products", "Product"),
    # comms
    "EmailTemplate": ("domains.comms.models.marketing", "EmailTemplate"),
    # suppliers
    "SupplierProfile": ("domains.suppliers.models.suppliers", "SupplierProfile"),
    # country
    "CountryConfig": ("domains.country.models.countries", "CountryConfig"),
    # logistics
    "LogisticsPartner": ("domains.logistics.models.logistics", "LogisticsPartner"),
    "LogisticsPartnerServiceArea": ("domains.logistics.models.logistics", "LogisticsPartnerServiceArea"),
    "LogisticsPricingProfile": ("domains.logistics.models.logistics", "LogisticsPricingProfile"),
    "LogisticsVehicleRule": ("domains.logistics.models.logistics", "LogisticsVehicleRule"),
    "Shipment": ("domains.logistics.models.logistics", "Shipment"),
    "ShipmentEvent": ("domains.logistics.models.logistics", "ShipmentEvent"),
    # orders
    "Order": ("domains.orders.models.order_entities", "Order"),
    "OrderItem": ("domains.orders.models.order_entities", "OrderItem"),
    "OrderLogisticsAllocation": ("domains.orders.models.order_entities", "OrderLogisticsAllocation"),
    # hr
    "Employee": ("domains.hr.models.employee_models", "Employee"),
    "Office": ("domains.hr.models.employee_models", "Office"),
    # finance (for treasury integration)
    "Account": ("domains.finance.models.finance", "Account"),
    "AccountGroup": ("domains.finance.models.finance", "AccountGroup"),
    "TreasuryAccount": ("domains.finance.models.finance", "TreasuryAccount"),
    # promotions
    "Banner": ("domains.promotions.models.promotions", "Banner"),
    "FlashSale": ("domains.promotions.models.promotions", "FlashSale"),
    "FlashSaleItem": ("domains.comms.models.marketing", "FlashSaleItem"),
    "Coupon": ("domains.promotions.models.promotions", "Coupon"),
    # supplier products (country-specific)
    "SupplierProduct": ("domains.suppliers.models.products", "SupplierProduct"),
}

_CACHE: dict[str, object] = {}


def get_model(name: str):
    """Lazily import and return a domain model class."""
    if name in _CACHE:
        return _CACHE[name]
    if name not in _REGISTRY:
        raise AttributeError(f"Model {name!r} not in seed registry")
    module_path, class_name = _REGISTRY[name]
    mod = _importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    _CACHE[name] = cls
    return cls
