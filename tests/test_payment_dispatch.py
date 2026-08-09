"""Registry-driven payment dispatch — no DB required.

These tests pin the architecture rule that adding a payment gateway must NOT
require editing ``services``/``controllers``/``routers``: a gateway is usable
solely by registering its ``create``/``confirm``/``webhook`` operations in
``providers/payments/config.py``.
"""
from __future__ import annotations

import asyncio

import pytest

from providers.payments.base import (
    OPERATION_CONFIRM,
    OPERATION_CREATE,
    OPERATION_WEBHOOK,
    PAYMENT_PROVIDER_REGISTRY,
    dispatch_provider_operation,
)

BUILT_IN_GATEWAYS = ["stripe", "tap", "paytabs", "paypal", "thawani", "generic"]


def test_all_built_in_gateways_registered_with_operations():
    for code in BUILT_IN_GATEWAYS:
        assert code in PAYMENT_PROVIDER_REGISTRY, f"{code} not registered"
        ops = PAYMENT_PROVIDER_REGISTRY[code].operations
        assert OPERATION_CREATE in ops
        assert OPERATION_CONFIRM in ops
        assert OPERATION_WEBHOOK in ops


def test_dispatch_routes_to_registered_sync_handler():
    reg = PAYMENT_PROVIDER_REGISTRY["stripe"]
    original = reg.operations[OPERATION_CREATE]
    captured: dict = {}

    def fake(body, user, db):
        captured["args"] = (body, user)
        return {"dispatched": True}

    reg.operations[OPERATION_CREATE] = fake
    try:
        result = asyncio.run(
            dispatch_provider_operation(
                "stripe", OPERATION_CREATE, {"order_id": 1}, {"role": "customer"}, None
            )
        )
        assert result == {"dispatched": True}
        assert captured["args"] == ({"order_id": 1}, {"role": "customer"})
    finally:
        reg.operations[OPERATION_CREATE] = original


def test_dispatch_routes_to_registered_async_handler():
    reg = PAYMENT_PROVIDER_REGISTRY["stripe"]
    original = reg.operations[OPERATION_WEBHOOK]

    async def fake_webhook(request, db):
        return {"webhook": True}

    reg.operations[OPERATION_WEBHOOK] = fake_webhook
    try:
        result = asyncio.run(dispatch_provider_operation("stripe", OPERATION_WEBHOOK, None, None))
        assert result == {"webhook": True}
    finally:
        reg.operations[OPERATION_WEBHOOK] = original


def test_dispatch_unknown_gateway_raises():
    with pytest.raises(NotImplementedError):
        asyncio.run(dispatch_provider_operation("no-such-gateway", OPERATION_CREATE))
