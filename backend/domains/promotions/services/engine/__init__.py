"""Promotions engine services — promotion engine, flash sales, controllers."""
from __future__ import annotations

from domains.promotions.services.engine.promotion_service import (
    calculate_order_tier_discount,
    get_promotion_config,
    list_promotion_tiers,
    preview_order_tier_discount,
    record_order_tier_ledger,
    update_promotion_config,
)
from domains.promotions.services.engine.promotion_engine_service import (
    ensure_promotion_tables,
    get_or_create_config,
)
from domains.promotions.services.engine.admin_promotions_write_service import (
    banner_to_dict,
    create_banner,
    create_coupon,
    create_flash_sale,
    delete_banner,
    get_promotion_config as get_promotion_config_admin,
    list_banners_paginated,
    list_coupons,
    list_flash_sales,
    list_promotion_tiers as list_promotion_tiers_admin,
    update_banner,
    update_flash_sale,
)

__all__ = [
    "calculate_order_tier_discount",
    "banner_to_dict",
    "create_banner",
    "create_coupon",
    "create_flash_sale",
    "delete_banner",
    "ensure_promotion_tables",
    "get_or_create_config",
    "get_promotion_config",
    "get_promotion_config_admin",
    "list_banners_paginated",
    "list_coupons",
    "list_flash_sales",
    "list_promotion_tiers",
    "list_promotion_tiers_admin",
    "preview_order_tier_discount",
    "record_order_tier_ledger",
    "update_banner",
    "update_flash_sale",
    "update_promotion_config",
]
