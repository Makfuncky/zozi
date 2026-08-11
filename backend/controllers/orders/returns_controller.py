"""controllers.orders.returns_controller controller.

Business logic is delegated to services.orders.returns_controller_service (routers -> controllers -> services)."""

from services.orders.returns_controller_service import (
    _attach_return_request_context, _build_list_page_payload, _build_supplier_review_state, _build_supplier_review_state_for_item, _capture_exc, _default_supplier_review_entry,
    _normalized_return_window_days, _order_delivery_reference, _order_items, _order_return_window_days, _parse_supplier_review_state, _return_request_item_summaries,
    _serialize_supplier_return_request, _supplier_ids_for_order, _supplier_owned_items, _utcnow, bulk_update_return_requests, create_return_request,
    get_return_request, list_return_requests, list_supplier_return_requests, logger, update_return_request, update_supplier_return_request
)

__all__ = [
    "_attach_return_request_context", "_build_list_page_payload", "_build_supplier_review_state", "_build_supplier_review_state_for_item", "_capture_exc", "_default_supplier_review_entry",
    "_normalized_return_window_days", "_order_delivery_reference", "_order_items", "_order_return_window_days", "_parse_supplier_review_state", "_return_request_item_summaries",
    "_serialize_supplier_return_request", "_supplier_ids_for_order", "_supplier_owned_items", "_utcnow", "bulk_update_return_requests", "create_return_request",
    "get_return_request", "list_return_requests", "list_supplier_return_requests", "logger", "update_return_request", "update_supplier_return_request"
]
