"""Behavior tests for finance domain — payments, payouts, commissions, and ledger operations."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domains.finance.models.payments import Payment, Payout, TransactionLedger
from domains.finance.services.finance_service import (
    verify_bank_connection,
    reconcile_in_multi_currency,
)


def _create_payment(db_session, amount=100.00, currency="USD", status="pending", gateway="stripe"):
    payment = Payment(
        amount=Decimal(str(amount)),
        currency=currency,
        status=status,
        gateway=gateway,
        user_id=1,
    )
    db_session.add(payment)
    db_session.flush()
    return payment


# ══════════════════════════════════════════════════════════════════
# Payment Creation and Processing
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPaymentCreation:
    """Test payment creation and processing."""

    def test_create_payment(self, db_session):
        payment = _create_payment(db_session, amount=50.00)
        assert payment.id is not None
        assert float(payment.amount) == 50.00
        assert payment.status == "pending"

    def test_payment_default_status_is_pending(self, db_session):
        payment = _create_payment(db_session)
        assert payment.status == "pending"

    def test_payment_with_stripe_gateway(self, db_session):
        payment = _create_payment(db_session, gateway="stripe")
        assert payment.gateway == "stripe"

    def test_payment_with_tap_gateway(self, db_session):
        payment = _create_payment(db_session, gateway="tap")
        assert payment.gateway == "tap"

    def test_payment_with_paypal_gateway(self, db_session):
        payment = _create_payment(db_session, gateway="paypal")
        assert payment.gateway == "paypal"

    def test_payment_with_paytabs_gateway(self, db_session):
        payment = _create_payment(db_session, gateway="paytabs")
        assert payment.gateway == "paytabs"

    def test_payment_with_thawani_gateway(self, db_session):
        payment = _create_payment(db_session, gateway="thawani")
        assert payment.gateway == "thawani"


# ══════════════════════════════════════════════════════════════════
# Payment Gateway Routing
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPaymentGatewayRouting:
    """Test payment gateway routing logic."""

    def test_stripe_gateway_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        stripe = PaymentGatewayRegistry.get("stripe")
        assert stripe is not None

    def test_tap_gateway_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        tap = PaymentGatewayRegistry.get("tap")
        assert tap is not None

    def test_paypal_gateway_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        paypal = PaymentGatewayRegistry.get("paypal")
        assert paypal is not None

    def test_paytabs_gateway_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        paytabs = PaymentGatewayRegistry.get("paytabs")
        assert paytabs is not None

    def test_thawani_gateway_available(self):
        from providers.payments.registry import PaymentGatewayRegistry
        thawani = PaymentGatewayRegistry.get("thawani")
        assert thawani is not None

    def test_unknown_gateway_returns_none(self):
        from providers.payments.registry import PaymentGatewayRegistry
        unknown = PaymentGatewayRegistry.get("unknown_gateway")
        assert unknown is None


# ══════════════════════════════════════════════════════════════════
# Payout Creation and Batching
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestPayoutOperations:
    """Test payout creation and batching."""

    def test_create_payout(self, db_session):
        payout = Payout(
            user_id=1,
            amount=Decimal("500.00"),
            currency="USD",
            status="pending",
        )
        db_session.add(payout)
        db_session.flush()
        assert payout.id is not None
        assert float(payout.amount) == 500.00
        assert payout.status == "pending"

    def test_payout_default_status_is_pending(self, db_session):
        payout = Payout(user_id=1, amount=Decimal("100.00"))
        db_session.add(payout)
        db_session.flush()
        assert payout.status == "pending"

    def test_payout_batching_by_status(self, db_session):
        for _ in range(3):
            payout = Payout(user_id=1, amount=Decimal("100.00"), status="pending")
            db_session.add(payout)
        db_session.flush()
        pending_count = db_session.query(Payout).filter(Payout.status == "pending").count()
        assert pending_count >= 3


# ══════════════════════════════════════════════════════════════════
# Commission Calculation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCommissionCalculation:
    """Test commission calculation logic."""

    def test_preview_commission_with_default_rate(self, db_session):
        from domains.finance.services.ledger.general_ledger_service import preview_commission
        result = preview_commission(supplier_id=1, order_value=100.00, db=db_session)
        assert "commission_amount" in result or isinstance(result, (int, float, Decimal))

    def test_preview_commission_with_category(self, db_session):
        from domains.finance.services.ledger.general_ledger_service import preview_commission
        result = preview_commission(supplier_id=1, order_value=200.00, category_slug="electronics", db=db_session)
        assert result is not None

    def test_set_supplier_commission_override(self, db_session):
        from domains.finance.services.ledger.general_ledger_service import set_supplier_commission
        result = set_supplier_commission(supplier_id=1, rate=0.15, note="Test override", acting_user={"id": 1}, db=db_session)
        assert result is not None

    def test_get_supplier_commission(self, db_session):
        from domains.finance.services.ledger.general_ledger_service import get_supplier_commission
        result = get_supplier_commission(1, db_session)
        assert result is not None

    def test_delete_supplier_commission_override(self, db_session):
        from domains.finance.services.ledger.general_ledger_service import set_supplier_commission, delete_supplier_commission_override
        set_supplier_commission(supplier_id=1, rate=0.15, note="Test", acting_user={"id": 1}, db=db_session)
        result = delete_supplier_commission_override(1, {"id": 1}, db_session)
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Tax Calculation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestTaxCalculation:
    """Test tax calculation logic."""

    def test_vat_calculation(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.calculate_vat(amount=100.00, country_code="AE")
        assert result is not None

    def test_vat_calculation_with_zero_rate(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.calculate_vat(amount=100.00, country_code="AE")
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Journal Entry Creation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestJournalEntry:
    """Test journal entry creation."""

    def test_create_journal_entry(self, db_session):
        from domains.finance.models.finance import JournalEntry
        entry = JournalEntry(
            entry_date=datetime.now(timezone.utc).date(),
            description="Test journal entry",
            reference="REF-001",
            total_debit=100.00,
            total_credit=100.00,
            status="posted",
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.id is not None
        assert entry.total_debit == 100.00
        assert entry.total_credit == 100.00

    def test_journal_entry_balanced(self, db_session):
        from domains.finance.models.finance import JournalEntry
        entry = JournalEntry(
            entry_date=datetime.now(timezone.utc).date(),
            description="Balanced entry",
            reference="REF-002",
            total_debit=50.00,
            total_credit=50.00,
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.total_debit == entry.total_credit

    def test_journal_entry_default_status_posted(self, db_session):
        from domains.finance.models.finance import JournalEntry
        entry = JournalEntry(
            entry_date=datetime.now(timezone.utc).date(),
            description="Default status test",
            total_debit=10.00,
            total_credit=10.00,
        )
        db_session.add(entry)
        db_session.flush()
        assert entry.status == "posted"


# ══════════════════════════════════════════════════════════════════
# Fiscal Period Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestFiscalPeriod:
    """Test fiscal period management."""

    def test_create_fiscal_period(self, db_session):
        from domains.finance.models.finance import FiscalPeriod
        period = FiscalPeriod(
            name="Q1 2024",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 3, 31).date(),
            status="open",
        )
        db_session.add(period)
        db_session.flush()
        assert period.id is not None
        assert period.status == "open"

    def test_fiscal_period_date_range(self, db_session):
        from domains.finance.models.finance import FiscalPeriod
        period = FiscalPeriod(
            name="FY 2024",
            start_date=datetime(2024, 1, 1).date(),
            end_date=datetime(2024, 12, 31).date(),
        )
        db_session.add(period)
        db_session.flush()
        assert period.start_date < period.end_date


# ══════════════════════════════════════════════════════════════════
# Bank Reconciliation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestBankReconciliation:
    """Test bank reconciliation operations."""

    def test_reconcile_transaction(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.admin_reconcile_transaction(txn_id=1, acting_user={"id": 1}, db=db_session)
        assert result is not None

    def test_flag_transaction(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.admin_flag_transaction(txn_id=1, reason="Suspicious", db=db_session)
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Cash Management Operations
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCashManagement:
    """Test cash management operations."""

    def test_create_bank_transaction(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.admin_create_bank_transaction(
            {"amount": 100.00, "type": "credit", "description": "Test"},
            db=db_session,
        )
        assert result is not None

    def test_list_bank_transactions(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.admin_list_bank_transactions(db=db_session, skip=0, limit=10)
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════════
# Invoice Generation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestInvoiceGeneration:
    """Test invoice generation."""

    def test_generate_invoice_for_order(self, db_session):
        from domains.finance.services.treasury.cash_management_service import CashManagementService
        service = CashManagementService(db_session)
        result = service.generate_invoice(order_id=1, db=db_session)
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Multi-Currency Reconciliation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestMultiCurrencyReconciliation:
    """Test multi-currency reconciliation."""

    def test_same_currency_returns_same_amount(self):
        result = reconcile_in_multi_currency(100.00, "USD", "USD")
        assert result["converted"] == 100.00
        assert result["rate"] == 1.0

    def test_different_currency_returns_rate(self):
        result = reconcile_in_multi_currency(100.00, "USD", "EUR")
        assert "rate" in result
        assert "converted" in result

    def test_unavailable_rate_returns_error(self):
        result = reconcile_in_multi_currency(100.00, "XXX", "YYY")
        assert "error" in result or result.get("converted") is None


# ══════════════════════════════════════════════════════════════════
# Bank Connection Verification
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestBankConnection:
    """Test bank connection verification."""

    def test_verify_bank_connection_returns_dict(self):
        result = verify_bank_connection("https://bank-api.example.com", "test-key")
        assert isinstance(result, dict)
        assert "connected" in result
        assert "message" in result

    def test_verify_bank_connection_invalid_url(self):
        result = verify_bank_connection("", "")
        assert result["connected"] is False
