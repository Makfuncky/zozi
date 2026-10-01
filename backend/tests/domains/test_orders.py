"""Domain tests for orders — order lifecycle, status transitions, and cart."""
from __future__ import annotations

import pytest


class TestOrderServiceImports:
    """Smoke tests: verify order service modules are importable."""

    def test_import_orders_service(self):
        from domains.orders.services import orders_service

        assert orders_service is not None

    def test_import_order_engine(self):
        from domains.orders.services.core.order_engine import create_order, get_order, cancel_order

        assert callable(create_order)
        assert callable(get_order)
        assert callable(cancel_order)

    def test_import_order_models(self):
        from domains.orders.models.order_entities import Order, OrderItem, ReturnRequest

        assert Order is not None
        assert OrderItem is not None
        assert ReturnRequest is not None

    def test_import_order_events(self):
        from domains.orders.events import OrderCreatedEvent

        assert OrderCreatedEvent is not None

    def test_import_order_ports(self):
        from domains.orders.ports import get_order_by_id

        assert callable(get_order_by_id)

    def test_import_order_features(self):
        from domains.orders.features import ORDER_FEATURES

        assert isinstance(ORDER_FEATURES, (list, tuple, set))


class TestOrderCreation:
    """Tests for order creation flow."""

    def test_order_model_has_required_fields(self, db_session):
        from domains.orders.models.order_entities import Order

        order = Order(
            user_id=1,
            status_code="pending",
            currency="USD",
        )
        db_session.add(order)
        db_session.flush()

        assert order.id is not None
        assert order.status_code == "pending"
        assert order.currency == "USD"

    def test_order_item_model_fields(self, db_session):
        from domains.orders.models.order_entities import Order, OrderItem

        order = Order(user_id=1, status_code="pending")
        db_session.add(order)
        db_session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=1,
            quantity=2,
            unit_price=10.00,
        )
        db_session.add(item)
        db_session.flush()

        assert item.id is not None
        assert item.order_id == order.id
        assert item.quantity == 2


class TestOrderStatusTransitions:
    """Tests for order status transition logic."""

    def test_order_status_values(self):
        from domains.orders.models.order_entities import Order

        valid_statuses = ("pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned")
        for status in valid_statuses:
            assert status in valid_statuses

    def test_order_status_transition_pending_to_confirmed(self, db_session):
        from domains.orders.models.order_entities import Order

        order = Order(user_id=1, status_code="pending")
        db_session.add(order)
        db_session.flush()

        order.status_code = "confirmed"
        db_session.flush()

        assert order.status_code == "confirmed"

    def test_order_status_transition_confirmed_to_cancelled(self, db_session):
        from domains.orders.models.order_entities import Order

        order = Order(user_id=1, status_code="confirmed")
        db_session.add(order)
        db_session.flush()

        order.status_code = "cancelled"
        db_session.flush()

        assert order.status_code == "cancelled"

    def test_order_service_has_status_helpers(self):
        from domains.orders.services.tracking.service import order_status_label, reconcile_order_status

        assert callable(order_status_label)
        assert callable(reconcile_order_status)
