"""Suppliers domain — public facade.

Exports the public API for the suppliers domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "SupplierService": ("domains.suppliers.services.supplier_service", "SupplierService"),
    "SupplierShared": ("domains.suppliers.services.supplier_shared", "SupplierShared"),
    "SupplierProfileService": ("domains.suppliers.services.profile.supplier_profile_service", "SupplierProfileService"),
    "SupplierProductsService": ("domains.suppliers.services.products.supplier_products_service", "SupplierProductsService"),
    "SupplierOrdersService": ("domains.suppliers.services.orders.supplier_orders_service", "SupplierOrdersService"),
    "SupplierHealthService": ("domains.suppliers.services.health.supplier_health_service", "SupplierHealthService"),
    "SupplierHealthEngine": ("domains.suppliers.services.health.supplier_health_engine", "SupplierHealthEngine"),
    "BadgeService": ("domains.suppliers.services.badges.badge_service", "BadgeService"),
    "BadgeWriteService": ("domains.suppliers.services.badges.badge_write_service", "BadgeWriteService"),
    "LegalContractService": ("domains.suppliers.services.contracts.legal_contract_service", "LegalContractService"),
    "SupplierDocumentsService": ("domains.suppliers.services.documents.supplier_documents_service", "SupplierDocumentsService"),
    "SupplierOnboardingService": ("domains.suppliers.services.onboarding.supplier_onboarding_service", "SupplierOnboardingService"),
    "SupplierBankAccountService": ("domains.suppliers.services.profile.supplier_bank_account_service", "SupplierBankAccountService"),
    "SupplierPayoutsService": ("domains.suppliers.services.profile.supplier_payouts_service", "SupplierPayoutsService"),
    # models
    "Supplier": ("domains.suppliers.models.suppliers", "Supplier"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.suppliers' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
