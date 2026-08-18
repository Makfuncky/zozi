"""controllers.commerce.coupons_controller controller.

Business logic is delegated to services.commerce.coupons_service (routers -> controllers -> services)."""  # noqa: E501

from domains.orders.services.coupons_service import _calculate_discount
from domains.orders.services.coupons_service import _calculate_total_from_items
from domains.orders.services.coupons_service import _delete_coupon_record
from domains.orders.services.coupons_service import _get_coupon_by_code
from domains.orders.services.coupons_service import _normalize_coupon_code
from domains.orders.services.coupons_service import _validate_coupon_for_total
from domains.orders.services.coupons_service import build_coupon_quote
from domains.orders.services.coupons_service import create_coupon
from domains.orders.services.coupons_service import delete_coupon
from domains.orders.services.coupons_service import delete_coupon_by_code
from domains.orders.services.coupons_service import list_coupons
from domains.orders.services.coupons_service import logger
from domains.orders.services.coupons_service import validate_coupon

__all__ = [
    "_calculate_discount", "_calculate_total_from_items", "_delete_coupon_record", "_get_coupon_by_code", "_normalize_coupon_code", "_validate_coupon_for_total",
    "build_coupon_quote", "create_coupon", "delete_coupon", "delete_coupon_by_code", "list_coupons", "logger",
    "validate_coupon"
]
