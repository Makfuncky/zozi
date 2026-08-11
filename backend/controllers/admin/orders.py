"""controllers.admin.orders controller.

Business logic is delegated to services.admin.orders_service (routers -> controllers -> services)."""

from services.admin.orders_service import (
    _build_list_page_payload, _can_staff_override_order_status, _order_to_dict, bulk_delete_orders_admin, bulk_update_order_status_admin, delete_order_admin,
    get_all_orders, refund_order, update_order_status, update_order_tracking
)

__all__ = [
    "_build_list_page_payload", "_can_staff_override_order_status", "_order_to_dict", "bulk_delete_orders_admin", "bulk_update_order_status_admin", "delete_order_admin",
    "get_all_orders", "refund_order", "update_order_status", "update_order_tracking"
]
