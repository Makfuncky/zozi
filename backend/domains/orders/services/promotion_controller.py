"""controllers.commerce.promotion_controller controller.

Business logic is delegated to services.commerce.promotion_service (routers -> controllers -> services)."""

from domains.orders.services.promotion_service import _ALLOWED_STACKING_MODES
from domains.orders.services.promotion_service import _ensure_promotion_tables
from domains.orders.services.promotion_service import _find_matching_tier
from domains.orders.services.promotion_service import _get_or_create_config
from domains.orders.services.promotion_service import _seed_default_tiers
from domains.orders.services.promotion_service import _serialize_config
from domains.orders.services.promotion_service import _serialize_tier
from domains.orders.services.promotion_service import _validate_tier_payload
from domains.orders.services.promotion_service import calculate_order_tier_discount
from domains.orders.services.promotion_service import create_promotion_tier
from domains.orders.services.promotion_service import delete_promotion_tier
from domains.orders.services.promotion_service import get_promotion_config
from domains.orders.services.promotion_service import list_promotion_tiers
from domains.orders.services.promotion_service import preview_order_tier_discount
from domains.orders.services.promotion_service import record_order_tier_ledger
from domains.orders.services.promotion_service import update_promotion_config
from domains.orders.services.promotion_service import update_promotion_tier

__all__ = [
    "_ALLOWED_STACKING_MODES", "_ensure_promotion_tables", "_find_matching_tier", "_get_or_create_config", "_seed_default_tiers", "_serialize_config",
    "_serialize_tier", "_validate_tier_payload", "calculate_order_tier_discount", "create_promotion_tier", "delete_promotion_tier", "get_promotion_config",
    "list_promotion_tiers", "preview_order_tier_discount", "record_order_tier_ledger", "update_promotion_config", "update_promotion_tier"
]
