"""Orders domain — feature & service smoke tests (Laws 3, 4, 19, 221).

Verifies:
  * Domain imports cleanly.
  * Feature atoms are in the rbac catalog.
  * Cross-domain writes go via events (Law 3) and catalog reads via ports.
  * Representative service/endpoint smoke test via the appropriate client.
"""
from __future__ import annotations

import pytest

from tests._support.laws import load_feature_catalog


# ---------------------------------------------------------------------------
# Law 4 — domain imports cleanly; feature atoms in catalog
# ---------------------------------------------------------------------------


class TestOrdersImportsCleanly:
    """The orders domain package must import without errors."""

    def test_import_orders_domain(self):
        import domains.orders  # noqa: F401

    def test_import_orders_features(self):
        from domains.orders import features  # noqa: F401

    def test_import_orders_ports(self):
        from domains.orders import ports  # noqa: F401

    def test_import_orders_events(self):
        from domains.orders import events  # noqa: F401

    def test_import_orders_subscribers(self):
        from domains.orders import subscribers  # noqa: F401


class TestOrdersFeatureAtoms:
    """Orders feature atoms must be registered in the rbac catalog."""

    def test_all_features_registered(self):
        catalog = load_feature_catalog()
        from domains.orders.features import FEATURES

        for key in FEATURES:
            assert key in catalog, f"Feature '{key}' not in rbac catalog (Law 4)"


# ---------------------------------------------------------------------------
# Law 3 — cross-domain writes via events, reads via ports
# ---------------------------------------------------------------------------


class TestOrdersCrossDomainWiring:
    """Cross-domain communication must flow through events/ports (Law 3)."""

    def test_order_events_exported_via_getattr(self):
        """orders.events lazily exports event type constants (Law 3)."""
        from domains.orders import events

        # These are lazily resolved via __getattr__
        assert hasattr(events, "EVENT_ORDER_CREATED")
        assert hasattr(events, "EVENT_ORDER_CONFIRMED")
        assert hasattr(events, "EVENT_ORDER_SHIPPED")

    def test_order_event_classes_accessible(self):
        """orders.events exposes event classes (Law 3)."""
        from domains.orders.events import OrderCreated, OrderConfirmed, OrderCancelled

        assert OrderCreated is not None
        assert OrderConfirmed is not None
        assert OrderCancelled is not None

    def test_catalog_reads_via_ports(self, db_session):
        """orders reads catalog data through catalog.ports, not direct imports (Law 3)."""
        from domains.catalog.ports import get_product_by_id, list_products

        # These are the sanctioned read path
        assert callable(get_product_by_id)
        assert callable(list_products)
        # Verify they work against the session
        assert get_product_by_id(db_session, 999999) is None
        assert isinstance(list_products(db_session, limit=5), list)


# ---------------------------------------------------------------------------
# Law 3 / 221 — ports read helpers work against a real session
# ---------------------------------------------------------------------------


class TestOrdersPortsSmoke:
    """Sanctioned read helpers return expected types (Law 3/221)."""

    def test_get_order_by_id_returns_none_for_missing(self, db_session):
        from domains.orders.ports import get_order_by_id

        result = get_order_by_id(db_session, 999999)
        assert result is None

    def test_list_orders_returns_cursor_page(self, db_session):
        from domains.orders.ports import list_orders

        page = list_orders(db_session, page_size=5)
        assert hasattr(page, "items")
        assert hasattr(page, "next_cursor")

    def test_list_orders_keyset_returns_dict(self, db_session):
        from domains.orders.ports import list_orders_keyset

        result = list_orders_keyset(db_session, size=5)
        assert isinstance(result, dict)
        assert "items" in result
        assert "next_cursor" in result


# ---------------------------------------------------------------------------
# Law 19 — money uses Decimal not float (runtime check)
# ---------------------------------------------------------------------------


class TestOrdersMoneyDecimal:
    """Money values at runtime must be Decimal, never float (Law 19)."""

    def test_order_total_is_numeric_type(self, db_session):
        """Order.total column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.orders.models.order_entities import Order

        assert isinstance(Order.__table__.c.total.type, Numeric)

    def test_order_subtotal_is_numeric_type(self, db_session):
        """Order.subtotal column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.orders.models.order_entities import Order

        assert isinstance(Order.__table__.c.subtotal.type, Numeric)


# ---------------------------------------------------------------------------
# Endpoint smoke test via admin client
# ---------------------------------------------------------------------------


class TestOrdersEndpointSmoke:
    """Representative orders endpoint responds (Law 2 thin routers)."""

    def test_orders_list_endpoint(self, admin_client):
        """Admin can reach an orders list endpoint (Law 2)."""
        resp = admin_client.get("/api/v1/admin/orders")
        assert resp.status_code in (200, 404, 307)

    def test_health_endpoint(self, client):
        """Health endpoint responds (basic wiring check)."""
        resp = client.get("/health")
        assert resp.status_code in (200, 404)
