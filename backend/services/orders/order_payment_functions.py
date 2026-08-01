"""
Order Payment Functions — Order-related payment operations (TODO: W3 violation fix).

These functions are currently in `controllers/payments_controller.py` but belong
logically in this service layer following proper architecture boundaries.

ARCHITECTURE: W3 VIOLATION - TODO
=================================
This module currently re-exports from `controllers.payments_controller` to avoid
breaking changes during refactor. The functions should be moved here permanently.

Functions to be migrated:
- normalize_checkout_payment_method (line 469 in payments_controller.py)
- is_checkout_payment_method_allowed (line 480)
- build_order_payment_snapshot (line 772)
- apply_order_status_change (line 2087)
- confirm_cash_on_delivery_order (line 2205)
- _order_holds_inventory (line 922)
- _event_publisher (line 2166) - should come from events module

Related constants to be moved:
- INVENTORY_HELD_STATUSES
- INVENTORY_RELEASE_STATUSES
- COD_PAYMENT_METHOD
- SUPPORTED_CHECKOUT_PAYMENT_METHODS
- ORDER_PAYMENT_METHOD_GATEWAY_MAP

TODO: Move these functions from controllers/payments_controller.py to this module.
Update routers/payments.py to import from services.orders.order_payment_functions
instead of controllers.payments_controller.
"""

from __future__ import annotations

from controllers.payments_controller import (  # noqa: TID252
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

# FIXME: This module violates W3 rule - it imports from controllers.
# The TODO above documents the planned permanent fix.