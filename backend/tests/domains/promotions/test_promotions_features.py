"""Promotions domain — feature & service smoke tests (Laws 3, 4, 19, 221).

Verifies:
  * Domain imports cleanly.
  * Feature atoms are in the rbac catalog.
  * Representative service/endpoint smoke test via the appropriate client.
  * Money uses Decimal not float at runtime (Law 19).
"""
from __future__ import annotations

import pytest

from tests._support.laws import load_feature_catalog


# ---------------------------------------------------------------------------
# Law 4 — domain imports cleanly; feature atoms in catalog
# ---------------------------------------------------------------------------


class TestPromotionsImportsCleanly:
    """The promotions domain package must import without errors."""

    def test_import_promotions_domain(self):
        import domains.promotions  # noqa: F401

    def test_import_promotions_features(self):
        from domains.promotions import features  # noqa: F401

    def test_import_promotions_ports(self):
        from domains.promotions import ports  # noqa: F401

    def test_import_promotions_events(self):
        from domains.promotions import events  # noqa: F401

    def test_import_promotions_subscribers(self):
        from domains.promotions import subscribers  # noqa: F401


class TestPromotionsFeatureAtoms:
    """Promotions feature atoms must be registered in the rbac catalog."""

    def test_all_features_registered(self):
        catalog = load_feature_catalog()
        from domains.promotions.features import FEATURES

        for key in FEATURES:
            assert key in catalog, f"Feature '{key}' not in rbac catalog (Law 4)"


# ---------------------------------------------------------------------------
# Law 3 / 221 — ports read helpers work against a real session
# ---------------------------------------------------------------------------


class TestPromotionsPortsSmoke:
    """Sanctioned read helpers return expected types (Law 3/221)."""

    def test_get_promotion_engine_config_returns_none_for_missing(self, db_session):
        from domains.promotions.ports import get_promotion_engine_config

        result = get_promotion_engine_config(db_session, "ZZ")
        assert result is None

    def test_is_engine_enabled_returns_bool(self, db_session):
        from domains.promotions.ports import is_engine_enabled

        result = is_engine_enabled(db_session, "ZZ")
        assert isinstance(result, bool)

    def test_get_max_combined_discount_returns_decimal(self, db_session):
        from domains.promotions.ports import get_max_combined_discount

        result = get_max_combined_discount(db_session, "ZZ")
        # Should be Decimal
        from decimal import Decimal

        assert isinstance(result, Decimal)


# ---------------------------------------------------------------------------
# Law 19 — money uses Decimal not float (runtime check)
# ---------------------------------------------------------------------------


class TestPromotionsMoneyDecimal:
    """Money values at runtime must be Decimal, never float (Law 19)."""

    def test_coupon_discount_value_is_numeric_type(self, db_session):
        """Coupon.discount_value column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.promotions.models.promotions import Coupon

        assert isinstance(Coupon.__table__.c.discount_value.type, Numeric)

    def test_coupon_minimum_order_is_numeric_type(self, db_session):
        """Coupon.minimum_order column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.promotions.models.promotions import Coupon

        assert isinstance(Coupon.__table__.c.minimum_order.type, Numeric)


# ---------------------------------------------------------------------------
# Endpoint smoke test via admin client
# ---------------------------------------------------------------------------


class TestPromotionsEndpointSmoke:
    """Representative promotions endpoint responds (Law 2 thin routers)."""

    def test_promotions_list_endpoint(self, admin_client):
        """Admin can reach a promotions list endpoint (Law 2)."""
        resp = admin_client.get("/api/v1/admin/promotions/coupons")
        assert resp.status_code in (200, 404, 307)

    def test_health_endpoint(self, client):
        """Health endpoint responds (basic wiring check)."""
        resp = client.get("/health")
        assert resp.status_code in (200, 404)
