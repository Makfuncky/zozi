"""Catalog domain — public facade.

Exports the public API for the catalog domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "ProductsService": ("domains.catalog.services.products.products_service", "ProductsService"),
    "CategoriesService": ("domains.catalog.services.categories.categories_service", "CategoriesService"),
    "CategoryService": ("domains.catalog.services.categories.category_service", "CategoryService"),
    "SearchService": ("domains.catalog.services.search.search_service", "SearchService"),
    "AISearchService": ("domains.catalog.services.search.ai_search_service", "AISearchService"),
    "AIUploadService": ("domains.catalog.services.ai_upload_service", "AIUploadService"),
    "ProductDiscountService": ("domains.catalog.services.products.product_discount_service", "ProductDiscountService"),
    "ProductModerationService": ("domains.catalog.services.products.product_moderation_service", "ProductModerationService"),
    "ProductVerificationService": ("domains.catalog.services.products.product_verification_service", "ProductVerificationService"),
    "VariantConfigService": ("domains.catalog.services.variants.variant_config_service", "VariantConfigService"),
    # models
    "Product": ("domains.catalog.models.products", "Product"),
    "Category": ("domains.catalog.models.products", "Category"),
    "Coupon": ("domains.promotions.models.promotions", "Coupon"),
    # functions
    "get_product_by_id": ("domains.catalog.services.products.products_service", "get_product_by_id"),
    "list_products": ("domains.catalog.services.products.products_service", "list_products"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.catalog' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
