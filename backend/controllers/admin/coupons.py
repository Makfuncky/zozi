"""controllers.admin.coupons controller.

Business logic is delegated to services.admin.coupons_service (routers -> controllers -> services)."""

from services.admin.coupons_service import (
    create_coupon, delete_coupon, list_coupons, update_coupon
)

__all__ = [
    "create_coupon", "delete_coupon", "list_coupons", "update_coupon"
]
