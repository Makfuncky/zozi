"""finance domain ORM models.

Canonical model definitions live in:
  - ``domains.finance.models.general_ledger`` — ledger, invoices, treasury, etc.
  - ``domains.finance.models.commission`` — commission agreements & rates
  - ``domains.finance.models.erp`` — ERP/logistics-trading documents
  - ``domains.finance.models.payments`` — payments, payouts, gateway connections

SQLAlchemy mappers must be registered exactly *once* per ``__tablename__``, so
this module is a pure re-export shim: existing importers
(``from domains.finance.models.finance import Account``) keep working without
re-registering any table.
"""
from __future__ import annotations

from domains.finance.models.general_ledger import *  # noqa: F401,F403
from domains.finance.models.commission import (  # noqa: F401,F403
    CommissionAgreement,
    CommissionCategoryRate,
    CommissionLedgerEntry,
    ProductCommissionOverride,
)
from domains.finance.models.payments import (  # noqa: F401,F403
    LogisticsPartnerPayout,
    Payment,
    PaymentGatewayConnection,
    PaymentReconciliationRun,
    Payout,
)

__all__ = [
    "Accrual", "Account", "AccountBalance", "AccountGroup",
    "APBill", "APLedger", "ARInvoice", "ARLedgerEntry",
    "AutomationLog", "AutomationRule",
    "BankAccount", "BankMappingRule", "BankReconciliation",
    "BankStatementImport", "BankStatementLine", "BankTransaction",
    "Budget", "CashAccount", "CashFlowForecast", "CashPositionSnapshot",
    "CashTransaction", "CostCenter", "Customer",
    "FinanceAuditLog", "FinanceAutomationLog", "FinancialReport",
    "FiscalPeriod", "FixedAsset",
    "GatewaySettlementSchedule",
    "Invoice", "InvoiceItem",
    "JournalEntry", "JournalEntryLine",
    "Payout", "PayoutBatch", "PayoutBatchItem", "PendingJournalEntry",
    "Payment", "PaymentGatewayConnection", "PaymentReconciliationRun",
    "RecurringTemplate", "RefundLedger",
    "ScannedExpense", "SupplierSettlement",
    "TransactionLedger", "TreasuryAccount", "TreasuryTransaction",
    "VATRemittance", "Vendor",
    "CommissionAgreement", "CommissionCategoryRate",
    "CommissionLedgerEntry", "ProductCommissionOverride",
    "LogisticsPartnerPayout",
]


def __getattr__(name: str):
    """Lazy re-export fallback for names not bound during re-entrant module load.

    When ``general_ledger`` re-enters ``finance`` during its own initialisation,
    only a subset of names are bound (the subset defined in ``general_ledger``
    before it reaches its ``from domains.finance.models.finance import X`` lines).
    This ``__getattr__`` binds the remaining names on first access after both
    modules have finished loading.
    """
    import importlib

    _gl = importlib.import_module("domains.finance.models.general_ledger")
    _gl_names = set(_gl.__all__) if hasattr(_gl, "__all__") else set()
    _finance_all = set(__all__)
    _missing = _finance_all - _gl_names - {
        "CommissionAgreement", "CommissionCategoryRate",
        "CommissionLedgerEntry", "ProductCommissionOverride",
        "LogisticsPartnerPayout", "Payment", "PaymentGatewayConnection",
        "PaymentReconciliationRun", "Payout",
    }

    if name in _missing:
        obj = getattr(_gl, name)
        globals()[name] = obj
        return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

