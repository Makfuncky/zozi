"""controllers.commerce.coupons_controller controller.

Business logic is delegated to services.commerce.coupons_service (routers -> controllers -> services)."""  # noqa: E501

from services.commerce.coupons_service import (
    _calculate_discount, _calculate_total_from_items, _delete_coupon_record, _get_coupon_by_code, _normalize_coupon_code, _validate_coupon_for_total,
    build_coupon_quote, create_coupon, delete_coupon, delete_coupon_by_code, list_coupons, logger,
    validate_coupon
)

__all__ = [
    "_calculate_discount", "_calculate_total_from_items", "_delete_coupon_record", "_get_coupon_by_code", "_normalize_coupon_code", "_validate_coupon_for_total",
    "build_coupon_quote", "create_coupon", "delete_coupon", "delete_coupon_by_code", "list_coupons", "logger",
    "validate_coupon"
]
