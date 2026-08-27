"""Promotions domain — public facade.

Exports the public API for the promotions domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "AdminPromotionService": ("domains.promotions.services.admin_promotion_service", "AdminPromotionService"),
    "FlashSaleService": ("domains.promotions.services.flash_sale_service", "FlashSaleService"),
    "FlashSaleWriteService": ("domains.promotions.services.flash_sale_write_service", "FlashSaleWriteService"),
    "PromotionsWriteService": ("domains.promotions.services.promotions_write_service", "PromotionsWriteService"),
    "PromotionAdminWriteService": ("domains.promotions.services.promotion_admin_write_service", "PromotionAdminWriteService"),
    "PromotionEngineService": ("domains.promotions.services.engine.promotion_engine_service", "PromotionEngineService"),
    "PromotionService": ("domains.promotions.services.engine.promotion_service", "PromotionService"),
    "BannerService": ("domains.promotions.services.banners.banner_service", "BannerService"),
    "BannerWriteService": ("domains.promotions.services.banners.banner_write_service", "BannerWriteService"),
    "BogoService": ("domains.promotions.services.bogo.bogo_service", "BogoService"),
    "CoinService": ("domains.promotions.services.coins.coin_service", "CoinService"),
    "PromotionPointsService": ("domains.promotions.services.coins.promotion_points_service", "PromotionPointsService"),
    "CouponService": ("domains.promotions.services.coupons.coupon_service", "CouponService"),
    # models
    "PromotionConfig": ("domains.promotions.models.promotion_config", "PromotionConfig"),
    "CouponUsage": ("domains.promotions.models.coupon_usage", "CouponUsage"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.promotions' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
