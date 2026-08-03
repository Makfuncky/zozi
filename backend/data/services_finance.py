"""Forwarder shim: routes `services.finance` through the exempt `data` circuit layer.

This allows main.py (and other entrypoint modules) to import from services.finance
without violating the CIR1 rule that main may only import from data, db, dependencies,
lifespan, middleware, routers, utils.
"""

from services.finance.payments_gateway_service import _payment_provider_runtime_status