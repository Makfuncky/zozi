"""finance domain ORM models.

Canonical model definitions live in:
  - ``domains.finance.models.general_ledger`` — ledger, invoices, treasury, etc.
  - ``domains.finance.models.commission`` — commission agreements & rates
  - ``domains.finance.models.erp`` — ERP/logistics-trading documents

SQLAlchemy mappers must be registered exactly *once* per ``__tablename__``, so
this module is a pure re-export shim: existing importers
(``from domains.finance.models.finance import Account``) keep working without
re-registering any table.
"""
from __future__ import annotations

from domains.finance.models.general_ledger import *  # noqa: F401,F403
from domains.finance.models.commission import *  # noqa: F401,F403

from domains.finance.models.general_ledger import (
    Accrual,
    Account,
    AccountBalance,
    AccountGroup,
    APBill,
    APLedger,
    ARInvoice,
    ARLedgerEntry,
    AutomationLog,
    AutomationRule,
    BankAccount,
    BankMappingRule,
    BankReconciliation,
    BankStatementImport,
    BankStatementLine,
    BankTransaction,
    Budget,
    CashAccount,
    CashFlowForecast,
    CashPositionSnapshot,
    CashTransaction,
    CostCenter,
    Customer,
    FinanceAuditLog,
    FinanceAutomationLog,
    FinancialReport,
    FiscalPeriod,
    FixedAsset,
    GatewaySettlementSchedule,
    Invoice,
    InvoiceItem,
    JournalEntry,
    JournalEntryLine,
    PayoutBatch,
    PayoutBatchItem,
    PendingJournalEntry,
    RecurringTemplate,
    RefundLedger,
    ScannedExpense,
    SupplierSettlement,
    TransactionLedger,
    TreasuryAccount,
    TreasuryTransaction,
    VATRemittance,
    Vendor,
)
from domains.finance.models.commission import (
    CommissionAgreement,
    CommissionCategoryRate,
    CommissionLedgerEntry,
    ProductCommissionOverride,
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
    "PayoutBatch", "PayoutBatchItem", "PendingJournalEntry",
    "RecurringTemplate", "RefundLedger",
    "ScannedExpense", "SupplierSettlement",
    "TransactionLedger", "TreasuryAccount", "TreasuryTransaction",
    "VATRemittance", "Vendor",
    "CommissionAgreement", "CommissionCategoryRate",
    "CommissionLedgerEntry", "ProductCommissionOverride",
]
