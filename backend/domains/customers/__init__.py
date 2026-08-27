"""Customers domain — public facade.

Exports the public API for the customers domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "CartService": ("domains.customers.services.cart_service", "CartService"),
    "CartWriteService": ("domains.customers.services.cart_write_service", "CartWriteService"),
    "CommerceReadService": ("domains.customers.services.commerce_read_service", "CommerceReadService"),
    "CommerceWriteService": ("domains.customers.services.commerce_write_service", "CommerceWriteService"),
    "CouponsService": ("domains.customers.services.coupons_service", "CouponsService"),
    "CouponsReadService": ("domains.customers.services.coupons_read_service", "CouponsReadService"),
    "CouponsWriteService": ("domains.customers.services.coupons_write_service", "CouponsWriteService"),
    "CustomerHealthService": ("domains.customers.services.customer_health_service", "CustomerHealthService"),
    "CustomerHealthEngine": ("domains.customers.services.customer_health_engine", "CustomerHealthEngine"),
    "CustomerHealthListService": ("domains.customers.services.customer_health_list_service", "CustomerHealthListService"),
    "ReviewsService": ("domains.customers.services.reviews_service", "ReviewsService"),
    "SearchService": ("domains.customers.services.search_service", "SearchService"),
    "WishlistService": ("domains.customers.services.wishlist_service", "WishlistService"),
    "WishlistReadService": ("domains.customers.services.wishlist_read_service", "WishlistReadService"),
    "WishlistWriteService": ("domains.customers.services.wishlist_write_service", "WishlistWriteService"),
    "RecommendationService": ("domains.customers.services.recommendations.recommendation_service", "RecommendationService"),
    "ZoziCoinsService": ("domains.customers.services.coins.zozi_coins_service", "ZoziCoinsService"),
    # models
    "CustomerSchema": ("domains.customers.models.customer_schema_models", "CustomerSchema"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.customers' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
