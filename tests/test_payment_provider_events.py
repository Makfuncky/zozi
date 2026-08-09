"""Tests for the event-based decoupling of the payment providers (CG1/CG2/CIR1).

These verify that:
  * The payment providers no longer import ``services``/``controllers`` at module level.
  * ``apply_order_status_change`` publishes a ``PaymentRefundedEvent`` (no direct
    services call) instead of creating the refund ledger inline.
  * The subscriber handlers (``services.payment_event_handlers``) drive ledger,
    cash, journal, cache and email side effects for the three payment events.
"""

import importlib
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "backend"
PROVIDERS = BACKEND / "providers" / "payments"

UPWARD_IMPORT_RE = re.compile(r'^\s*(from|import)\s+(services|controllers)\b', re.M)


def _import_provider_modules():
    mods = {}
    for name in ("_order", "paypal", "stripe", "tap", "thawani", "paytabs"):
        mod = importlib.import_module(f"providers.payments.{name}")
        mods[name] = mod
    return mods


def test_provider_modules_have_no_top_level_upward_imports():
    for path in PROVIDERS.glob("*.py"):
        if path.name in ("__init__.py", "_common.py", "config.py", "webhooks.py", "generic.py"):
            continue
        source = path.read_text(encoding="utf-8")
        matches = UPWARD_IMPORT_RE.findall(source)
        assert not matches, f"{path.name} still has upward import(s): {matches}"


def test_order_helper_no_controllers_cache_delegate():
    # The controllers.products_controller cache delegate must be gone (CIR1).
    source = (PROVIDERS / "_order.py").read_text(encoding="utf-8")
    assert "controllers.products_controller" not in source
    assert "bump_product_cache_version" in source


def test_apply_order_status_change_publishes_refunded_event():
    from events import PaymentRefundedEvent, _event_publisher

    captured = []
    _event_publisher.register_listener(PaymentRefundedEvent, captured.append)

    try:
        _order = importlib.import_module("providers.payments._order")
        order = MagicMock()
        order.id = 42
        order.user_id = 7
        db = MagicMock()
        refund_meta = {
            "source": "stripe_refund",
            "transaction_ref": "ch_1:refund",
            "description": "Stripe refund settled for order 42",
            "transaction_date": None,
        }
        _order.apply_order_status_change(order, "refunded", db, refund_meta=refund_meta)
        assert len(captured) == 1
        event = captured[0]
        assert isinstance(event, PaymentRefundedEvent)
        assert event.order_id == 42
        assert event.reason == "refund"
        assert event.refund_meta == refund_meta
    finally:
        _event_publisher._listeners[PaymentRefundedEvent].remove(captured.append)


def test_handle_payment_confirmed_card_payment_runs_services():
    from services import payment_event_handlers as handlers

    event = MagicMock()
    event.order_id = 10
    event.payment_method = "card"
    event.payment_gateway = "stripe"
    event.currency = "USD"
    event.amount = "25.00"
    db = MagicMock()

    with patch.object(handlers, "create_ledger_entries_for_order") as ledger, \
         patch.object(handlers, "log_card_payment_received") as card, \
         patch.object(handlers, "post_order_payment_journal") as journal, \
         patch.object(handlers, "bump_product_cache_version") as cache, \
         patch.object(handlers, "enqueue_payment_confirmed_email") as email, \
         patch.object(handlers, "Order") as Order:
        Order.query.filter.return_value.first.return_value = MagicMock()
        handlers.handle_payment_confirmed(event, db)

    ledger.assert_called_once()
    card.assert_called_once()
    journal.assert_called_once()
    cache.assert_called_once()
    email.assert_called_once_with(10, provider="stripe", message=None)


def test_handle_payment_confirmed_cod_skips_card_side_effects():
    from services import payment_event_handlers as handlers

    event = MagicMock()
    event.order_id = 11
    event.payment_method = "cod"
    event.payment_gateway = "cod"
    event.currency = "AED"
    event.amount = "40.00"
    db = MagicMock()

    with patch.object(handlers, "create_ledger_entries_for_order") as ledger, \
         patch.object(handlers, "log_card_payment_received") as card, \
         patch.object(handlers, "post_order_payment_journal") as journal, \
         patch.object(handlers, "bump_product_cache_version") as cache, \
         patch.object(handlers, "enqueue_payment_confirmed_email") as email, \
         patch.object(handlers, "Order") as Order:
        Order.query.filter.return_value.first.return_value = MagicMock()
        handlers.handle_payment_confirmed(event, db)

    ledger.assert_called_once()
    card.assert_not_called()
    journal.assert_not_called()
    cache.assert_called_once()
    email.assert_called_once_with(11, provider="cod", message=None)


def test_handle_payment_failed_enqueues_email():
    from services import payment_event_handlers as handlers

    event = MagicMock()
    event.order_id = 20
    event.provider = "tap"
    event.message = "boom"
    db = MagicMock()

    with patch.object(handlers, "enqueue_payment_failed_email") as email:
        handlers.handle_payment_failed(event, db)

    email.assert_called_once_with(20, provider="tap", message="boom")


def test_handle_payment_refunded_with_meta_runs_all():
    from services import payment_event_handlers as handlers

    event = MagicMock()
    event.order_id = 30
    event.reason = "refund"
    event.refund_meta = {
        "source": "paypal_refund",
        "transaction_ref": "txn1",
        "description": "desc",
        "transaction_date": None,
    }
    db = MagicMock()

    with patch.object(handlers, "create_refund_ledger_entry") as refund_ledger, \
         patch.object(handlers, "log_refund_bank_transaction") as bank, \
         patch.object(handlers, "enqueue_refund_processed_email") as email, \
         patch.object(handlers, "Order") as Order:
        Order.query.filter.return_value.first.return_value = MagicMock()
        handlers.handle_payment_refunded(event, db)

    refund_ledger.assert_called_once()
    bank.assert_called_once()
    email.assert_called_once_with(30, source="paypal_refund")


def test_handle_payment_refunded_without_meta_skips_bank_and_email():
    from services import payment_event_handlers as handlers

    event = MagicMock()
    event.order_id = 31
    event.reason = "cancellation"
    event.refund_meta = {}
    db = MagicMock()

    with patch.object(handlers, "create_refund_ledger_entry") as refund_ledger, \
         patch.object(handlers, "log_refund_bank_transaction") as bank, \
         patch.object(handlers, "enqueue_refund_processed_email") as email, \
         patch.object(handlers, "Order") as Order:
        Order.query.filter.return_value.first.return_value = MagicMock()
        handlers.handle_payment_refunded(event, db)

    refund_ledger.assert_called_once()
    bank.assert_not_called()
    email.assert_not_called()
