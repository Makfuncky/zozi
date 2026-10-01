"""Regression tests for general_ledger.py relationship lazy loading (DB-049)."""
from __future__ import annotations

import pytest
from sqlalchemy.orm import RelationshipProperty


def test_general_ledger_relationships_have_selectin_lazy():
    """All relationships in general_ledger.py must declare lazy='selectin'."""
    from domains.finance.models.general_ledger import (
        FiscalPeriod,
        TransactionLedger,
        SupplierSettlement,
        JournalEntry,
        JournalEntryLine,
        Account,
        AccountGroup,
        AccountBalance,
        FinancialReport,
        Invoice,
        InvoiceItem,
        RefundLedger,
        BankTransaction,
        VATRemittance,
        CashAccount,
        CashTransaction,
        TreasuryAccount,
        TreasuryTransaction,
        CashFlowForecast,
        CashPositionSnapshot,
        GatewaySettlementSchedule,
        PendingJournalEntry,
        PayoutBatch,
        PayoutBatchItem,
        BankMappingRule,
        BankStatementImport,
        BankStatementLine,
        FixedAsset,
        Accrual,
        ScannedExpense,
        AutomationRule,
        AutomationLog,
        Vendor,
        Customer,
        CostCenter,
        APBill,
        ARInvoice,
        BankAccount,
        Budget,
        BankReconciliation,
        RecurringTemplate,
        FinanceAuditLog,
        FinanceAutomationLog,
    )

    model_classes = [
        FiscalPeriod,
        TransactionLedger,
        SupplierSettlement,
        JournalEntry,
        JournalEntryLine,
        Account,
        AccountGroup,
        AccountBalance,
        FinancialReport,
        Invoice,
        InvoiceItem,
        RefundLedger,
        BankTransaction,
        VATRemittance,
        CashAccount,
        CashTransaction,
        TreasuryAccount,
        TreasuryTransaction,
        CashFlowForecast,
        CashPositionSnapshot,
        GatewaySettlementSchedule,
        PendingJournalEntry,
        PayoutBatch,
        PayoutBatchItem,
        BankMappingRule,
        BankStatementImport,
        BankStatementLine,
        FixedAsset,
        Accrual,
        ScannedExpense,
        AutomationRule,
        AutomationLog,
        Vendor,
        Customer,
        CostCenter,
        APBill,
        ARInvoice,
        BankAccount,
        Budget,
        BankReconciliation,
        RecurringTemplate,
        FinanceAuditLog,
        FinanceAutomationLog,
    ]

    violations = []
    for model_cls in model_classes:
        for attr_name, attr in model_cls.__dict__.items():
            if isinstance(attr, RelationshipProperty):
                lazy = attr.lazy
                if lazy != 'selectin':
                    violations.append(
                        f"{model_cls.__name__}.{attr_name} has lazy={lazy!r}, expected 'selectin'"
                    )

    assert not violations, (
        "Relationships missing lazy='selectin' (Law 45 / DB-049):\n"
        + "\n".join(violations)
    )


def test_general_ledger_imports_without_error():
    """Smoke test: general_ledger models import cleanly."""
    from domains.finance.models import general_ledger

    assert hasattr(general_ledger, 'JournalEntry')
    assert hasattr(general_ledger, 'Account')
    assert hasattr(general_ledger, 'TransactionLedger')
