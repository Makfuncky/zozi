"""Orders core service — backward-compatible shim.

Code has been moved to:
  - order_engine: order lifecycle (create, preview, get, cancel)
  - order_admin: admin operations (tracking, scan receipt, confirmations)
  - order_dtos: DTO definitions
  - order_bulk: bulk operations
"""
from domains.orders.services.core.order_engine import *  # noqa: F401,F403
from domains.orders.services.core.order_admin import *  # noqa: F401,F403
from domains.orders.services.core.order_dtos import *  # noqa: F401,F403
from domains.orders.services.core.bulk import *  # noqa: F401,F403

__all__ = (
    # order_engine exports
    "create_order",
    "preview_order",
    "get_orders",
    "get_order",
    "cancel_order",
    "confirm_order_scan_receipt",
    "get_order_tracking",
    "respond_to_shipment_confirmation",
    "confirm_order_receipt_scan",
    "get_order_invoice",
)
