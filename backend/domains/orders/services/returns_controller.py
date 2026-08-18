"""controllers.orders.returns_controller controller.

Business logic is delegated to services.orders.returns_controller_service (routers -> controllers -> services)."""

from domains.orders.services.returns_controller_service import _attach_return_request_context
from domains.orders.services.returns_controller_service import _build_list_page_payload
from domains.orders.services.returns_controller_service import _build_supplier_review_state
from domains.orders.services.returns_controller_service import _build_supplier_review_state_for_item
from domains.orders.services.returns_controller_service import _capture_exc
from domains.orders.services.returns_controller_service import _default_supplier_review_entry
from domains.orders.services.returns_controller_service import _normalized_return_window_days
from domains.orders.services.returns_controller_service import _order_delivery_reference
from domains.orders.services.returns_controller_service import _order_items
from domains.orders.services.returns_controller_service import _order_return_window_days
from domains.orders.services.returns_controller_service import _parse_supplier_review_state
from domains.orders.services.returns_controller_service import _return_request_item_summaries
from domains.orders.services.returns_controller_service import _serialize_supplier_return_request
from domains.orders.services.returns_controller_service import _supplier_ids_for_order
from domains.orders.services.returns_controller_service import _supplier_owned_items
from domains.orders.services.returns_controller_service import _utcnow
from domains.orders.services.returns_controller_service import bulk_update_return_requests
from domains.orders.services.returns_controller_service import create_return_request
from domains.orders.services.returns_controller_service import get_return_request
from domains.orders.services.returns_controller_service import list_return_requests
from domains.orders.services.returns_controller_service import list_supplier_return_requests
from domains.orders.services.returns_controller_service import logger
from domains.orders.services.returns_controller_service import update_return_request
from domains.orders.services.returns_controller_service import update_supplier_return_request

__all__ = [
    "_attach_return_request_context", "_build_list_page_payload", "_build_supplier_review_state", "_build_supplier_review_state_for_item", "_capture_exc", "_default_supplier_review_entry",
    "_normalized_return_window_days", "_order_delivery_reference", "_order_items", "_order_return_window_days", "_parse_supplier_review_state", "_return_request_item_summaries",
    "_serialize_supplier_return_request", "_supplier_ids_for_order", "_supplier_owned_items", "_utcnow", "bulk_update_return_requests", "create_return_request",
    "get_return_request", "list_return_requests", "list_supplier_return_requests", "logger", "update_return_request", "update_supplier_return_request"
]
