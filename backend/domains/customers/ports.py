"""customers domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.customers.models`` or ``domains.customers.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

# Cross-domain re-exports (sanctioned READ surface per Law 3).
# Shipping quotes are owned by the orders domain; re-exported here so the
# customer module routers import them from customers.ports instead of
# directly from domains.orders.services.
from domains.orders.services.cart_legacy_service import (  # noqa: F401
    CartShippingQuoteRequest,
    get_cart_shipping_quote,
)

__all__ = [
    "CartShippingQuoteRequest",
    "get_cart_shipping_quote",
]
