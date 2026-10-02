"""Tests for orders domain event subscribers (FILE-110 / WIR-029 / WIR-028).

Verifies that subscriber handlers are callable and that the module uses the
canonical ``event_bus`` (not the deprecated ``EventPublisher``) for
cross-domain event routing (WIR-028 consolidation).
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from domains.orders.subscribers import (
    _on_order_cancelled,
    _on_order_confirmed,
    _on_order_created,
    _on_order_delivered,
    _on_order_shipped,
    register_orders_subscribers,
)


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_event(**kwargs):
    """Return a simple namespace-like event with the given attributes."""
    return type("Event", (), kwargs)()


# ── architectural verification ───────────────────────────────────────────────


class TestWIR028UsesCanonicalEventBus:
    """WIR-028: subscribers must register on the canonical event_bus."""

    def test_no_event_publisher_import_in_module(self):
        """subscribers.py must not import the deprecated EventPublisher."""
        import domains.orders.subscribers as mod

        source = inspect.getsource(mod)
        assert "EventPublisher" not in source, (
            "subscribers.py must not import or reference EventPublisher (WIR-028)"
        )

    def test_registers_via_event_bus_subscribe(self):
        """register_orders_subscribers must call event_bus.subscribe for each handler."""
        with patch(
            "domains.orders.subscribers.subscribe"
        ) as mock_subscribe:
            register_orders_subscribers()
            assert mock_subscribe.call_count == 5

    def test_no_get_db_session_references_in_handlers(self):
        """Handler source must not reference the removed _get_db_session helper."""
        handlers = [
            _on_order_created,
            _on_order_confirmed,
            _on_order_shipped,
            _on_order_delivered,
            _on_order_cancelled,
        ]
        for handler in handlers:
            source = inspect.getsource(handler)
            assert "_get_db_session" not in source, (
                f"{handler.__name__} must not reference _get_db_session"
            )


# ── smoke tests ──────────────────────────────────────────────────────────────


class TestSubscriberSmoke:
    """Handlers must be callable without raising."""

    def test_on_order_created_callable(self):
        event = _make_event(order_id=1, user_id=42)
        _on_order_created(event)  # must not raise

    def test_on_order_confirmed_callable(self):
        event = _make_event(order_id=2, confirmed_by=99)
        _on_order_confirmed(event)  # must not raise

    def test_on_order_shipped_callable(self):
        event = _make_event(order_id=3, tracking_number="TRK123")
        _on_order_shipped(event)  # must not raise

    def test_on_order_delivered_callable(self):
        event = _make_event(order_id=4)
        _on_order_delivered(event)  # must not raise

    def test_on_order_cancelled_callable(self):
        event = _make_event(order_id=5, reason="customer request")
        _on_order_cancelled(event)  # must not raise

    def test_handler_returns_early_on_missing_order_id(self):
        """Handlers must not crash when order_id is None."""
        for handler in [
            _on_order_created,
            _on_order_shipped,
            _on_order_delivered,
            _on_order_cancelled,
        ]:
            event = _make_event(order_id=None)
            handler(event)  # should not raise


# ── event-bus contract test (WIR-028) ───────────────────────────────────────


def test_register_uses_event_bus_not_publisher():
    """register_orders_subscribers must call event_bus.subscribe, not EventPublisher."""
    with patch(
        "domains.orders.subscribers.subscribe"
    ) as mock_subscribe:
        register_orders_subscribers()
        assert mock_subscribe.call_count == 5
        # Verify all calls use event_bus.subscribe (not EventPublisher.register_listener)
        for call in mock_subscribe.call_args_list:
            args = call[0]
            assert len(args) == 2  # event_type, handler
