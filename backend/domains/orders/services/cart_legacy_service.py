"""Broker re-exporting the legacy cart service surface.

``cart_legacy_service`` was merged into ``domains.orders.services.cart.service``
(see that module's header: "Merged from: cart_service.py, cart_legacy_service.py,
cart_write_service.py"). This thin module preserves the original import path
``domains.orders.services.cart_legacy_service`` so historical callers keep working
(Law 3 sanctioned re-export).
"""
from domains.orders.services.cart.service import *  # noqa: F401,F403
from domains.orders.services.cart.service import (  # noqa: F401
    CartShippingQuoteRequest,
    get_cart_shipping_quote,
)
