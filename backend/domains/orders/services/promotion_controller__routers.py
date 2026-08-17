"""controllers.commerce.promotion_controller controller.

Business logic is delegated to services.commerce.promotion_service (routers -> controllers -> services)."""

from domains.orders.services.promotion_service import (
    _ALLOWED_STACKING_MODES, _ensure_promotion_tables, _find_matching_tier, _get_or_create_config, _seed_default_tiers, _serialize_config,
    _serialize_tier, _validate_tier_payload, calculate_order_tier_discount, create_promotion_tier, delete_promotion_tier, get_promotion_config,
    list_promotion_tiers, preview_order_tier_discount, record_order_tier_ledger, update_promotion_config, update_promotion_tier
)

__all__ = [
    "_ALLOWED_STACKING_MODES", "_ensure_promotion_tables", "_find_matching_tier", "_get_or_create_config", "_seed_default_tiers", "_serialize_config",
    "_serialize_tier", "_validate_tier_payload", "calculate_order_tier_discount", "create_promotion_tier", "delete_promotion_tier", "get_promotion_config",
    "list_promotion_tiers", "preview_order_tier_discount", "record_order_tier_ledger", "update_promotion_config", "update_promotion_tier"
]
