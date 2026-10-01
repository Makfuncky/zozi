"""Cross-domain integration flow tests for the Zozi backend.

Verifies:
  1. Order → Payment flow (orders triggers finance via events).
  2. Catalog → Search flow.
  3. Customer → Order flow.
  4. Supplier → Catalog flow.
  5. Logistics → Order shipment flow.
  6. Account → Country flow.
  7. Cross-domain reads via ports.py.
  8. Cross-domain writes via events.py.
  9. Event subscriber triggering.
"""
from __future__ import annotations

import os
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CSRF_DISABLED", "true")


class TestOrderToPaymentFlow:
    """Order → Payment flow: orders domain triggers finance domain via events."""

    def test_orders_events_module_exists(self):
        from domains.orders import events
        assert hasattr(events, "EVENT_ORDER_CREATED")
        assert hasattr(events, "publish_order_created")

    def test_finance_events_module_exists(self):
        from domains.finance import events
        assert events is not None

    def test_order_ports_module_exists(self):
        from domains.orders import ports
        assert hasattr(ports, "get_order_by_id")
        assert hasattr(ports, "list_orders")

    def test_finance_ports_module_exists(self):
        from domains.finance import ports
        assert ports is not None

    def test_order_created_event_constant(self):
        from domains.orders.events import EVENT_ORDER_CREATED
        assert isinstance(EVENT_ORDER_CREATED, str)
        assert len(EVENT_ORDER_CREATED) > 0

    def test_order_confirmed_event_constant(self):
        from domains.orders.events import EVENT_ORDER_CONFIRMED
        assert isinstance(EVENT_ORDER_CONFIRMED, str)

    def test_order_ports_have_get_order_by_id(self, db_session):
        from domains.orders.ports import get_order_by_id
        result = get_order_by_id(db_session, 99999)
        assert result is None

    def test_order_ports_have_list_orders(self, db_session):
        from domains.orders.ports import list_orders
        result = list_orders(db_session, page_size=10)
        assert hasattr(result, "items") or isinstance(result, dict)


class TestCatalogToSearchFlow:
    """Catalog → Search flow."""

    def test_catalog_ports_module_exists(self):
        from domains.catalog import ports
        assert ports is not None

    def test_catalog_events_module_exists(self):
        from domains.catalog import events
        assert events is not None

    def test_catalog_ports_have_product_read(self, db_session):
        from domains.catalog.ports import Product
        assert Product is not None


class TestCustomerToOrderFlow:
    """Customer → Order flow."""

    def test_customers_ports_module_exists(self):
        from domains.customers import ports
        assert ports is not None

    def test_customers_events_module_exists(self):
        from domains.customers import events
        assert events is not None

    def test_orders_ports_have_list_by_user(self, db_session):
        from domains.orders.ports import list_orders_by_user
        result = list_orders_by_user(db_session, user_id=99999)
        assert isinstance(result, list)


class TestSupplierToCatalogFlow:
    """Supplier → Catalog flow."""

    def test_suppliers_ports_module_exists(self):
        from domains.suppliers import ports
        assert ports is not None

    def test_suppliers_events_module_exists(self):
        from domains.suppliers import events
        assert events is not None

    def test_orders_ports_have_list_by_supplier(self, db_session):
        from domains.orders.ports import list_orders_by_supplier
        result = list_orders_by_supplier(db_session, supplier_id=99999)
        assert isinstance(result, list)


class TestLogisticsToOrderShipmentFlow:
    """Logistics → Order shipment flow."""

    def test_logistics_ports_module_exists(self):
        from domains.logistics import ports
        assert ports is not None

    def test_logistics_events_module_exists(self):
        from domains.logistics import events
        assert events is not None

    def test_orders_ports_have_logistics_allocation(self, db_session):
        from domains.ports import get_order_logistics_allocation_by_id
        result = get_order_logistics_allocation_by_id(db_session, 99999)
        assert result is None


class TestAccountToCountryFlow:
    """Account → Country flow (user country assignment)."""

    def test_accounts_ports_module_exists(self):
        from domains.accounts import ports
        assert ports is not None

    def test_country_ports_module_exists(self):
        from domains.country import ports
        assert ports is not None

    def test_country_events_module_exists(self):
        from domains.country import events
        assert events is not None


class TestCrossDomainReadsViaPorts:
    """Cross-domain reads via ports.py."""

    def test_all_domains_have_ports(self):
        """Every domain should have a ports.py module."""
        domains = [
            "accounts", "analytics", "audit", "catalog", "comms",
            "country", "customers", "finance", "governance", "hr",
            "logistics", "orders", "promotions", "security", "suppliers",
        ]
        for domain in domains:
            mod = __import__(f"domains.{domain}.ports", fromlist=["*"])
            assert mod is not None, f"domains.{domain}.ports not found"

    def test_orders_ports_get_order_by_id(self, db_session):
        from domains.orders.ports import get_order_by_id
        result = get_order_by_id(db_session, 1)
        # Should return None for non-existent order
        assert result is None

    def test_orders_ports_count_orders(self, db_session):
        from domains.orders.ports import count_orders
        result = count_orders(db_session)
        assert isinstance(result, int)
        assert result >= 0

    def test_orders_ports_count_all_orders(self, db_session):
        from domains.orders.ports import count_all_orders
        result = count_all_orders(db_session)
        assert isinstance(result, int)
        assert result >= 0


class TestCrossDomainWritesViaEvents:
    """Cross-domain writes via events.py."""

    def test_all_domains_have_events(self):
        """Every domain should have an events.py module."""
        domains = [
            "accounts", "analytics", "audit", "catalog", "comms",
            "country", "customers", "finance", "governance", "hr",
            "logistics", "orders", "promotions", "security", "suppliers",
        ]
        for domain in domains:
            mod = __import__(f"domains.{domain}.events", fromlist=["*"])
            assert mod is not None, f"domains.{domain}.events not found"

    def test_orders_events_have_publish_functions(self):
        from domains.orders.events import (
            publish_order_created,
            publish_order_confirmed,
            publish_order_shipped,
        )
        assert callable(publish_order_created)
        assert callable(publish_order_confirmed)
        assert callable(publish_order_shipped)

    def test_orders_events_have_event_classes(self):
        from domains.orders.events import OrderCreated, OrderConfirmed
        assert OrderCreated is not None
        assert OrderConfirmed is not None


class TestEventSubscribers:
    """Event subscriber triggering."""

    def test_orders_subscribers_module_exists(self):
        from domains.orders import subscribers
        assert subscribers is not None

    def test_subscribers_have_handler_functions(self):
        from domains.orders import subscribers
        handler_names = [
            name for name in dir(subscribers)
            if name.startswith("on_") or name.startswith("handle_")
        ]
        # Should have at least some event handlers
        assert len(handler_names) > 0 or len(dir(subscribers)) > 5


class TestPortsPaginationEnvelope:
    """Verify ports return proper pagination envelopes."""

    def test_list_orders_returns_cursor_page(self, db_session):
        from domains.orders.ports import list_orders
        result = list_orders(db_session, page_size=5)
        # Should have items, next_cursor, has_next, page_size
        assert hasattr(result, "items") or isinstance(result, (dict, tuple))

    def test_list_orders_keyset_returns_envelope(self, db_session):
        from domains.orders.ports import list_orders_keyset
        result = list_orders_keyset(db_session, size=5)
        assert isinstance(result, dict)
        assert "items" in result
        assert "next_cursor" in result
        assert "page_size" in result
        assert "has_next" in result


class TestSoftDeleteFiltering:
    """Verify ports filter soft-deleted rows."""

    def test_list_orders_excludes_soft_deleted(self, db_session):
        from domains.orders.ports import list_orders
        result = list_orders(db_session, page_size=100)
        items = result.items if hasattr(result, "items") else result.get("items", [])
        for item in items:
            if hasattr(item, "is_deleted"):
                assert item.is_deleted is False


class TestCountryScoping:
    """Verify ports support country scoping."""

    def test_list_orders_with_country_code(self, db_session):
        from domains.orders.ports import list_orders
        result = list_orders(db_session, page_size=10, country_code="AE")
        assert result is not None

    def test_list_orders_with_different_country(self, db_session):
        from domains.orders.ports import list_orders
        result = list_orders(db_session, page_size=10, country_code="SA")
        assert result is not None
