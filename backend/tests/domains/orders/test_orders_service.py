"""Regression tests for FILE-47 — get_order_gateway DB-driven resolution.

Verifies:
  * Fallback to hardcoded map when no db session is provided (backward compat).
  * DB-driven gateway resolution via CountryConfig.payment_gateways_json when
    a session is provided (Law 118 — database-driven payment orchestration).
  * Graceful fallback when DB resolution raises or returns no gateway.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_order(country_code: str = "AE") -> MagicMock:
    """Return a minimal Order mock with a ``country_code`` attribute."""
    order = MagicMock()
    order.country_code = country_code
    return order


def _get_gateway():
    """Lazy import to avoid triggering FIELD_ENCRYPTION_SALT at collection time."""
    from domains.orders.services import orders_service as _svc
    return _svc.get_order_gateway


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------


class TestGetOrderGatewayFallback:
    """When db is None (or DB has no config), the hardcoded map is used."""

    def test_returns_stripe_for_ae_without_db(self):
        """AE maps to stripe in the hardcoded fallback."""
        order = _make_order("AE")
        assert _get_gateway()(order) == "stripe"

    def test_returns_tap_for_jo_without_db(self, monkeypatch: pytest.MonkeyPatch):
        """JO maps to tap in the hardcoded fallback when adapter is registered."""
        from providers.payments.registry import PaymentGatewayRegistry

        monkeypatch.setattr(PaymentGatewayRegistry, "get", lambda code: MagicMock() if code == "tap" else None)
        order = _make_order("JO")
        assert _get_gateway()(order) == "tap"

    def test_returns_paytabs_for_pk_without_db(self, monkeypatch: pytest.MonkeyPatch):
        """PK maps to paytabs in the hardcoded fallback when adapter is registered."""
        from providers.payments.registry import PaymentGatewayRegistry

        monkeypatch.setattr(PaymentGatewayRegistry, "get", lambda code: MagicMock() if code == "paytabs" else None)
        order = _make_order("PK")
        assert _get_gateway()(order) == "paytabs"

    def test_returns_stripe_for_unknown_country_without_db(self):
        """Unknown country codes fall back to stripe."""
        order = _make_order("XX")
        assert _get_gateway()(order) == "stripe"


class TestGetOrderGatewayDbResolution:
    """When db is provided, gateway is resolved from CountryConfig."""

    def test_returns_gateway_from_db_payment_gateways_json(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """DB-configured gateway overrides the hardcoded map."""
        from domains.orders.services import orders_service as _svc
        from providers.payments.registry import PaymentGatewayRegistry

        mock_config = MagicMock()
        mock_config.payment_gateways_json = '[{"gateway_id": "tap", "enabled": true}]'

        monkeypatch.setattr(_svc, "get_country_config", lambda db, code: mock_config)
        monkeypatch.setattr(PaymentGatewayRegistry, "get", lambda code: MagicMock() if code == "tap" else None)

        order = _make_order("SA")
        result = _get_gateway()(order, db=db_session)
        assert result == "tap"

    def test_falls_back_to_hardcoded_when_db_has_no_gateway_json(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """If the country exists but has no payment_gateways_json, fall back."""
        from domains.orders.services import orders_service as _svc

        mock_config = MagicMock()
        mock_config.payment_gateways_json = None

        monkeypatch.setattr(_svc, "get_country_config", lambda db, code: mock_config)

        order = _make_order("AE")
        assert _get_gateway()(order, db=db_session) == "stripe"

    def test_falls_back_to_hardcoded_when_db_has_empty_gateways(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """If payment_gateways_json is an empty list, fall back."""
        from domains.orders.services import orders_service as _svc

        mock_config = MagicMock()
        mock_config.payment_gateways_json = "[]"

        monkeypatch.setattr(_svc, "get_country_config", lambda db, code: mock_config)

        order = _make_order("KW")
        assert _get_gateway()(order, db=db_session) == "stripe"

    def test_falls_back_to_hardcoded_when_db_has_only_disabled_gateways(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """If all gateways are disabled, fall back."""
        from domains.orders.services import orders_service as _svc

        mock_config = MagicMock()
        mock_config.payment_gateways_json = '[{"gateway_id": "paytabs", "enabled": false}]'

        monkeypatch.setattr(_svc, "get_country_config", lambda db, code: mock_config)

        order = _make_order("QA")
        assert _get_gateway()(order, db=db_session) == "stripe"


class TestGetOrderGatewayErrorPath:
    """Error-path: DB resolution failures must not raise."""

    def test_db_exception_falls_back_gracefully(self, db_session: Session, monkeypatch: pytest.MonkeyPatch):
        """If get_country_config raises, the function falls back without raising."""
        from domains.orders.services import orders_service as _svc

        def _boom(db, code):  # noqa: ARG001
            raise RuntimeError("DB down")

        monkeypatch.setattr(_svc, "get_country_config", _boom)

        order = _make_order("AE")
        # Must not raise — falls back to hardcoded stripe
        assert _get_gateway()(order, db=db_session) == "stripe"
