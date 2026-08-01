"""Order-related services."""

from services.orders.order_payment_functions import (
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    is_checkout_payment_method_allowed,
    normalize_checkout_payment_method,
    _event_publisher,
    _order_holds_inventory,
)

__all__ = [
    "apply_order_status_change",
    "build_order_payment_snapshot",
    "confirm_cash_on_delivery_order",
    "is_checkout_payment_method_allowed",
    "normalize_checkout_payment_method",
    "_event_publisher",
    "_order_holds_inventory",
]

# NOTE: The imported functions currently re-export from controllers.payments_controller.
# See services/orders/order_payment_functions.py for the W3 violation TODO.