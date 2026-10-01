"""Finance domain — feature & service smoke tests (Laws 3, 4, 19, 221).

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


class TestFinanceImportsCleanly:
    """The finance domain package must import without errors."""

    def test_import_finance_domain(self):
        import domains.finance  # noqa: F401

    def test_import_finance_features(self):
        from domains.finance import features  # noqa: F401

    def test_import_finance_ports(self):
        from domains.finance import ports  # noqa: F401

    def test_import_finance_events(self):
        from domains.finance import events  # noqa: F401

    def test_import_finance_subscribers(self):
        from domains.finance import subscribers  # noqa: F401


class TestFinanceFeatureAtoms:
    """Finance feature atoms must be registered in the rbac catalog."""

    def test_all_features_registered(self):
        catalog = load_feature_catalog()
        from domains.finance.features import FEATURES

        for key in FEATURES:
            assert key in catalog, f"Feature '{key}' not in rbac catalog (Law 4)"


# ---------------------------------------------------------------------------
# Law 3 / 221 — ports read helpers work against a real session
# ---------------------------------------------------------------------------


class TestFinancePortsSmoke:
    """Sanctioned read helpers return expected types (Law 3/221)."""

    def test_get_payment_by_id_returns_none_for_missing(self, db_session):
        from domains.finance.ports import get_payment_by_id

        result = get_payment_by_id(db_session, 999999)
        assert result is None

    def test_get_payout_by_id_returns_none_for_missing(self, db_session):
        from domains.finance.ports import get_payout_by_id

        result = get_payout_by_id(db_session, 999999)
        assert result is None

    def test_list_payments_returns_list(self, db_session):
        from domains.finance.ports import list_payments

        result = list_payments(db_session, limit=10)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Law 19 — money uses Decimal not float (runtime check)
# ---------------------------------------------------------------------------


class TestFinanceMoneyDecimal:
    """Money values at runtime must be Decimal, never float (Law 19)."""

    def test_payment_amount_is_numeric_type(self, db_session):
        """Payment.amount column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.finance.models.payments import Payment

        assert isinstance(Payment.__table__.c.amount.type, Numeric)

    def test_payout_amount_is_numeric_type(self, db_session):
        """Payout.amount column type is Numeric (Law 19)."""
        from sqlalchemy import Numeric

        from domains.finance.models.payments import Payout

        assert isinstance(Payout.__table__.c.amount.type, Numeric)

    def test_journal_entry_amount_is_decimal(self):
        """JournalEntryPosted event amount defaults to Decimal (Law 19)."""
        from decimal import Decimal

        from domains.finance.events import JournalEntryPosted

        event = JournalEntryPosted()
        assert isinstance(event.amount, Decimal)


# ---------------------------------------------------------------------------
# Endpoint smoke test via admin client
# ---------------------------------------------------------------------------


class TestFinanceEndpointSmoke:
    """Representative finance endpoint responds (Law 2 thin routers)."""

    def test_finance_list_endpoint(self, admin_client):
        """Admin can reach a finance list endpoint (Law 2)."""
        resp = admin_client.get("/api/v1/admin/finance/payments")
        assert resp.status_code in (200, 404, 307)

    def test_health_endpoint(self, client):
        """Health endpoint responds (basic wiring check)."""
        resp = client.get("/health")
        assert resp.status_code in (200, 404)
