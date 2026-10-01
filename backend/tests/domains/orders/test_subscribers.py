"""Tests for orders domain event subscribers (FILE-110 / WIR-029).

Verifies that subscriber handlers no longer open synchronous DB sessions
via the removed ``_get_db_session`` helper and instead use the standard
``get_db_context`` context manager.
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


class TestWIR029SyncSessionRemoved:
    """WIR-029: subscribers must not use the custom sync _get_db_session helper."""

    def test_get_db_session_removed_from_module(self):
        """The removed _get_db_session helper must not exist in the module."""
        import domains.orders.subscribers as mod

        assert not hasattr(mod, "_get_db_session"), (
            "_get_db_session should be removed from subscribers.py"
        )

    def test_no_get_db_session_references_in_handlers(self):
        """Handler source must not reference _get_db_session."""
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

    def test_no_next_db_gen_in_handlers(self):
        """Handler source must not call next(db_gen) for manual session cleanup."""
        handlers = [
            _on_order_created,
            _on_order_confirmed,
            _on_order_shipped,
            _on_order_delivered,
            _on_order_cancelled,
        ]
        for handler in handlers:
            source = inspect.getsource(handler)
            assert "next(db_gen" not in source, (
                f"{handler.__name__} must not call next(db_gen)"
            )

    def test_handlers_use_get_db_context(self):
        """Each handler must use get_db_context as its session source."""
        import domains.orders.subscribers as mod

        source = inspect.getsource(mod)
        assert "get_db_context" in source, (
            "subscribers.py must import/use get_db_context"
        )


# ── smoke tests ──────────────────────────────────────────────────────────────


class TestSubscriberSmoke:
    """Handlers must be callable without raising when dependencies are mocked."""

    @patch("domains.orders.subscribers.get_db_context")
    def test_on_order_created_smoke(self, mock_get_db_context):
        mock_db = MagicMock()
        mock_get_db_context.return_value.__enter__ = MagicMock(
            return_value=mock_db
        )
        mock_get_db_context.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "domains.comms.services.notification_gateway.notify"
        ) as mock_notify:
            event = _make_event(order_id=1, user_id=42)
            _on_order_created(event)
            mock_notify.assert_called_once()

    @patch("domains.orders.subscribers.get_db_context")
    def test_on_order_confirmed_smoke(self, mock_get_db_context):
        mock_db = MagicMock()
        mock_get_db_context.return_value.__enter__ = MagicMock(
            return_value=mock_db
        )
        mock_get_db_context.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "domains.comms.services.notification_gateway.notify"
        ) as mock_notify:
            event = _make_event(order_id=2, confirmed_by=99)
            _on_order_confirmed(event)
            mock_notify.assert_called_once()

    @patch("domains.orders.subscribers.get_db_context")
    def test_on_order_shipped_smoke(self, mock_get_db_context):
        mock_db = MagicMock()
        mock_get_db_context.return_value.__enter__ = MagicMock(
            return_value=mock_db
        )
        mock_get_db_context.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "domains.comms.services.notification_gateway.notify"
        ) as mock_notify:
            event = _make_event(order_id=3, tracking_number="TRK123", user_id=1)
            _on_order_shipped(event)
            mock_notify.assert_called_once()

    @patch("domains.orders.subscribers.get_db_context")
    def test_on_order_delivered_smoke(self, mock_get_db_context):
        mock_db = MagicMock()
        mock_get_db_context.return_value.__enter__ = MagicMock(
            return_value=mock_db
        )
        mock_get_db_context.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "domains.comms.services.notification_gateway.notify"
        ) as mock_notify, patch(
            "domains.finance.ports.create_settlements_on_delivery"
        ) as mock_settlements:
            event = _make_event(order_id=4, user_id=1)
            _on_order_delivered(event)
            mock_notify.assert_called_once()
            mock_settlements.assert_called_once_with(db=mock_db, order_id=4)

    @patch("domains.orders.subscribers.get_db_context")
    def test_on_order_cancelled_smoke(self, mock_get_db_context):
        mock_db = MagicMock()
        mock_get_db_context.return_value.__enter__ = MagicMock(
            return_value=mock_db
        )
        mock_get_db_context.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "domains.comms.services.notification_gateway.notify"
        ) as mock_notify, patch(
            "domains.finance.ports.log_refund_bank_transaction"
        ) as mock_refund:
            event = _make_event(order_id=5, reason="customer request", user_id=1)
            _on_order_cancelled(event)
            mock_notify.assert_called_once()
            mock_refund.assert_called_once_with(
                db=mock_db, order_id=5, reason="customer request"
            )

    def test_register_orders_subscribers_registers_all_handlers(self):
        publisher = MagicMock()
        register_orders_subscribers(publisher)
        # 5 listeners should be registered
        assert publisher.register_listener.call_count == 5

    def test_handler_returns_early_on_missing_order_id(self):
        """Handlers must not crash when order_id is None."""
        for handler in [
            _on_order_created,
            _on_order_confirmed,
            _on_order_shipped,
            _on_order_delivered,
            _on_order_cancelled,
        ]:
            event = _make_event(order_id=None)
            handler(event)  # should not raise


# ── async-session contract test (WIR-029) ────────────────────────────────────


def test_async_session():
    """WIR-029: subscribers must not open blocking sync DB sessions via
    the removed _get_db_session helper; they must use get_db_context."""

    import domains.orders.subscribers as mod

    source = inspect.getsource(mod)

    # The removed helper must not appear anywhere in the module.
    assert "_get_db_session" not in source, (
        "subscribers.py must not define or call _get_db_session"
    )

    # The standard context manager must be referenced.
    assert "get_db_context" in source, (
        "subscribers.py must use get_db_context for DB session management"
    )
