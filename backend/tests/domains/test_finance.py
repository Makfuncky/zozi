"""Domain tests for finance — payments, ledger, and treasury services."""
from __future__ import annotations

import pytest


class TestFinanceServiceImports:
    """Smoke tests: verify finance service modules are importable."""

    def test_import_finance_service(self):
        from domains.finance.services import finance_service

        assert finance_service is not None

    def test_import_payment_orchestrator(self):
        from domains.finance.services.payments import payment_orchestrator

        assert payment_orchestrator is not None

    def test_import_payment_engine(self):
        from domains.finance.services.payments import payment_engine

        assert payment_engine is not None

    def test_import_general_ledger_service(self):
        from domains.finance.services.ledger import general_ledger_service

        assert general_ledger_service is not None

    def test_import_finance_models(self):
        from domains.finance.models.finance import Account, JournalEntry, TransactionLedger

        assert Account is not None
        assert JournalEntry is not None
        assert TransactionLedger is not None

    def test_import_finance_schemas(self):
        from domains.finance.schemas import finance_schemas

        assert finance_schemas is not None

    def test_import_finance_ports(self):
        from domains.finance.ports import get_payment_by_id

        assert callable(get_payment_by_id)

    def test_import_finance_features(self):
        from domains.finance.features import FINANCE_FEATURES

        assert isinstance(FINANCE_FEATURES, (list, tuple, set))


class TestPaymentOrchestrator:
    """Tests for payment orchestrator initialization and basic operations."""

    def test_orchestrator_has_gateway_wizard_step(self):
        from domains.finance.services.payments.payment_orchestrator import gateway_wizard_step

        assert callable(gateway_wizard_step)

    def test_payment_engine_has_required_functions(self):
        from domains.finance.services.payments import payment_engine

        assert hasattr(payment_engine, "apply_order_status_change")
        assert hasattr(payment_engine, "build_order_payment_snapshot")

    def test_payment_engine_normalize_gateway_code(self):
        from domains.finance.services.payments.payment_engine import _normalize_gateway_code

        assert _normalize_gateway_code("stripe") == "stripe"
        assert _normalize_gateway_code("STRIPE") == "stripe"


class TestLedgerService:
    """Tests for general ledger service basic operations."""

    def test_ledger_service_has_journal_entry_support(self):
        from domains.finance.services.ledger.general_ledger_service import JournalEntry

        assert JournalEntry is not None

    def test_ledger_service_has_account_model(self):
        from domains.finance.models.finance import Account

        assert Account is not None

    def test_finance_models_have_required_fields(self, db_session):
        from domains.finance.models.finance import Account

        account = Account(
            code="TEST-001",
            name="Test Account",
            account_type="asset",
            currency="USD",
        )
        db_session.add(account)
        db_session.flush()

        assert account.id is not None
        assert account.code == "TEST-001"
        assert account.name == "Test Account"
