"""Order Payment Functions — Order-related payment operations.

All payment functions are now imported from the service layer
(``services.finance.payments_gateway_service``), keeping this module
W3-compliant — no controller imports.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from services.finance.payments_gateway_service import (  # noqa: TID252
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    is_checkout_payment_method_allowed,
    normalize_checkout_payment_method,
    event_publisher as _event_publisher,
    order_holds_inventory as _order_holds_inventory,
)
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
]
