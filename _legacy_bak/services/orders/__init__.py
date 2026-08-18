"""Orders service package.

Re-exports order-payment functions and the fulfillment service so that the
``data.services_orders`` forwarder shim (and controllers that import package
level from ``services.orders``) can reach them without a circuit violation.
"""
from __future__ import annotations

from services.finance.order_payment_functions import (  # noqa: TID252
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    is_checkout_payment_method_allowed,
    normalize_checkout_payment_method,
    _event_publisher,
    _order_holds_inventory,
)
from .fulfillment_service import FulfillmentService
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "apply_order_status_change",
    "build_order_payment_snapshot",
    "confirm_cash_on_delivery_order",
    "is_checkout_payment_method_allowed",
    "normalize_checkout_payment_method",
    "_event_publisher",
    "_order_holds_inventory",
    "FulfillmentService",
]
