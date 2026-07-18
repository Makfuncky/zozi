from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["FiscalPeriod", "TransactionLedger", "SupplierSettlement", "JournalEntry", "JournalEntryLine",
           "Account", "AccountGroup", "AccountBalance", "FinancialReport",
           "Invoice", "InvoiceItem", "RefundLedger", "BankTransaction", "VATRemittance",
           "CashAccount", "CashTransaction", "TreasuryAccount", "TreasuryTransaction",
           "CashFlowForecast", "CashPositionSnapshot", "GatewaySettlementSchedule",
           "PendingJournalEntry", "PayoutBatch", "PayoutBatchItem",
           "ARLedgerEntry", "APLedger", "BankStatementImport", "BankStatementLine",
    "BankMappingRule", "FixedAsset", "Accrual", "ScannedExpense", "FinanceAutomationLog",
           "Vendor", "Customer", "CostCenter", "APBill", "ARInvoice", "BankAccount",
           "Budget", "BankReconciliation", "RecurringTemplate", "FinanceAuditLog"]


class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"
    __table_args__ = (
        UniqueConstraint("country_code", "period_year", "period_month", name="uq_fiscal_period"),
        Index("ix_fiscal_period_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=False, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    status = Column(String(20), default="open")  # open, closing, closed
    is_locked = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    closed_by_user = relationship("User", foreign_keys=[closed_by])


class TransactionLedger(Base):
    __tablename__ = "transaction_ledgers"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_transaction_ledger_amount_non_negative"),
        CheckConstraint("currency IN ('USD', 'EUR', 'GBP', 'AED', 'OMR', 'KWD', 'BHD', 'QAR', 'SAR', 'JOD')", name="chk_transaction_ledger_currency_valid"),
        Index("ix_transaction_ledger_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    logistics_partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    payment_method = Column(String(20), nullable=True)
    product_subtotal = Column(Numeric(12, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=True)
    delivery_pickup_charge = Column(Numeric(12, 2), nullable=True)
    delivery_dropoff_charge = Column(Numeric(12, 2), nullable=True)
    delivery_total = Column(Numeric(12, 2), nullable=True)
    vat_amount = Column(Numeric(12, 2), nullable=True)
    zozi_commission_rate = Column(Numeric(5, 4), nullable=True)
    zozi_commission = Column(Numeric(12, 2), nullable=True)
    net_supplier_amount = Column(Numeric(12, 2), nullable=True)
    net_logistics_amount = Column(Numeric(12, 2), nullable=True)
    net_zozi_amount = Column(Numeric(12, 2), nullable=True)
    cod_collected_amount = Column(Numeric(12, 2), nullable=True)
    cod_remittance_due = Column(Numeric(12, 2), nullable=True)
    settlement_status = Column(String(30), nullable=True)
    currency = Column(String(3), default="USD")
    transaction_type = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)
    balance_after = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class SupplierSettlement(Base):
    __tablename__ = "supplier_settlements"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="chk_supplier_settlement_gross_non_negative"),
        CheckConstraint("commission_amount >= 0", name="chk_supplier_settlement_commission_non_negative"),
        CheckConstraint("net_amount >= 0", name="chk_supplier_settlement_net_non_negative"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    ledger_id = Column(Integer, ForeignKey("transaction_ledgers.id"), nullable=True)
    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    gross_amount = Column(Numeric(12, 2), nullable=False)
    commission_amount = Column(Numeric(12, 2), nullable=True)
    commission_deducted = Column(Numeric(12, 2), nullable=True)
    commission_rate = Column(Numeric(5, 4), nullable=True)
    vat_on_commission = Column(Numeric(12, 2), nullable=True)
    net_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="pending")
    settled_at = Column(DateTime, nullable=True)
    eligible_at = Column(DateTime, nullable=True)
    bank_transaction_id = Column(Integer, nullable=True)
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        Index("ix_journal_entry_date", "entry_date"),
        Index("ix_journal_entry_ref", "reference_number"),
        Index("ix_journal_entry_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(DateTime, nullable=False)
    reference_number = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    country_code = Column(String(10), nullable=True)
    currency = Column(String(3), default="OMR")
    is_reconciled = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    period_id = Column(Integer, ForeignKey("fiscal_periods.id"), nullable=True, index=True)
    reversal_of_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
    period = relationship("FiscalPeriod", foreign_keys=[period_id])
    reversal_of = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversal_of_id])


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"
    __table_args__ = (Index("ix_jel_entry", "entry_id"), Index("ix_jel_account", "account_id"),
        CheckConstraint("amount >= 0", name="chk_jel_amount_non_negative"),
        CheckConstraint("side IN ('debit', 'credit')", name="chk_jel_side_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    cost_center_id = Column(Integer, ForeignKey("cost_centers.id"), nullable=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    side = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_code", "code"), Index("ix_accounts_group", "group_id"),
        CheckConstraint("normal_side IN ('debit', 'credit')", name="chk_account_normal_side_valid"),
    )
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    normal_side = Column(String(10), nullable=False)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    group = relationship("AccountGroup", back_populates="accounts")
    journal_lines = relationship("JournalEntryLine", back_populates="account")


class AccountGroup(Base):
    __tablename__ = "account_groups"
    __table_args__ = (Index("ix_account_groups_code", "code"), Index("ix_account_groups_order", "display_order"))
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    account_type = Column(String(30), nullable=False)
    normal_side = Column(String(10), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    accounts = relationship("Account", back_populates="group")


class AccountBalance(Base):
    __tablename__ = "account_balances"
    __table_args__ = (
        Index("ix_account_balance_account", "account_id"),
        Index("ix_account_balance_user", "user_id"),
        UniqueConstraint("account_id", "currency", name="uq_account_balance_account_currency"),
    )
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    balance = Column(Numeric(16, 4), default=0)
    currency = Column(String(3), default="OMR")
    last_entry_id = Column(Integer, nullable=True)
    last_entry_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    account = relationship("Account")
    user = relationship("User")


class ARLedgerEntry(Base):
    __tablename__ = "ar_ledger_entries"
    __table_args__ = (
        Index("ix_ar_ledger_user", "customer_id"),
        Index("ix_ar_ledger_status", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    entry_type = Column(String(20), nullable=False)  # invoice, payment, credit_note, refund
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")
    status = Column(String(20), default="open")  # open, partially_paid, paid, written_off
    due_date = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    customer = relationship("User", foreign_keys=[customer_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])


class APLedger(Base):
    __tablename__ = "ap_ledger_entries"
    __table_args__ = (
        Index("ix_ap_ledger_supplier", "supplier_id"),
        Index("ix_ap_ledger_status", "status"),
    )
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    settlement_id = Column(Integer, ForeignKey("supplier_settlements.id"), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    entry_type = Column(String(20), nullable=False)  # payable, payment, credit_note, adjustment
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")
    status = Column(String(20), default="open")  # open, partially_paid, closed, disputed
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    supplier = relationship("User", foreign_keys=[supplier_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    settlement = relationship("SupplierSettlement", foreign_keys=[settlement_id])


class FinancialReport(Base):
    __tablename__ = "financial_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    country_code = Column(String(10), nullable=True, index=True)
    data = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invoice_number = Column(String, unique=True, nullable=True)
    invoice_type = Column(String, default="sale")
    subtotal = Column(Numeric(12, 2), nullable=True)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    shipping_amount = Column(Numeric(12, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="USD")
    status = Column(String, default="pending")
    issued_at = Column(DateTime, default=_utcnow)
    due_at = Column(DateTime, nullable=True)
    picked_at = Column(DateTime, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    supplier = relationship("User", foreign_keys=[supplier_id], backref="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    line_total = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    invoice = relationship("Invoice", back_populates="items")


class RefundLedger(Base):
    __tablename__ = "refund_ledger"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    return_request_id = Column(Integer, ForeignKey("return_requests.id"), nullable=True)
    ledger_id = Column(Integer, nullable=True)
    bank_transaction_id = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    refund_reason = Column(Text, nullable=True)
    refund_method = Column(String, nullable=True)
    customer_refund_amount = Column(Numeric(12, 2), nullable=True)
    supplier_reversal = Column(Numeric(12, 2), nullable=True)
    logistics_reversal = Column(Numeric(12, 2), nullable=True)
    delivery_fee_reversal = Column(Numeric(12, 2), nullable=True)
    commission_reversal = Column(Numeric(12, 2), nullable=True)
    vat_adjustment = Column(Numeric(12, 2), nullable=True)
    vat_reversal = Column(Numeric(12, 2), nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    currency = Column(String(3), default="OMR")
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_ref = Column(String, nullable=True, index=True)
    source = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False)
    category = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="OMR")
    description = Column(Text, nullable=True)
    linked_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    linked_supplier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    linked_logistics_id = Column(Integer, nullable=True)
    linked_payout_id = Column(Integer, nullable=True)
    linked_refund_id = Column(Integer, nullable=True)
    reconciled = Column(Boolean, default=False)
    reconciled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    flagged = Column(Boolean, nullable=True, default=False)
    flag_reason = Column(Text, nullable=True)


class VATRemittance(Base):
    __tablename__ = "vat_remittances"
    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    vat_collected_amount = Column(Numeric(12, 2), nullable=True)
    vat_adjustment_amount = Column(Numeric(12, 2), nullable=True)
    amount_due = Column(Numeric(12, 2), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    amount_remitted = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")
    bank_transaction_id = Column(Integer, nullable=True)
    remitted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class CashAccount(Base):
    __tablename__ = "cash_accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    currency = Column(String(3), default="USD")
    balance = Column(Numeric(12, 2), default=0)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class CashTransaction(Base):
    __tablename__ = "cash_transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("cash_accounts.id"), nullable=False)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=True)
    description = Column(Text, nullable=True)
    reference = Column(String, nullable=True)
    category = Column(String, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class TreasuryAccount(Base):
    __tablename__ = "treasury_accounts"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    currency = Column(String(3), default="USD")
    gl_account_code = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    balance = Column(Numeric(12, 2), default=0)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class TreasuryTransaction(Base):
    __tablename__ = "treasury_transactions"
    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=True)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    reference = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    posted_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    net_cash_flow = Column(Numeric(12, 2), default=0)
    opening_balance = Column(Numeric(12, 2), default=0)
    closing_balance = Column(Numeric(12, 2), default=0)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class CashPositionSnapshot(Base):
    __tablename__ = "cash_position_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    snapshot_time = Column(DateTime, nullable=False)
    account_id = Column(Integer, ForeignKey("treasury_accounts.id"), nullable=False)
    balance = Column(Numeric(12, 2), default=0)
    currency = Column(String(3), default="USD")
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class GatewaySettlementSchedule(Base):
    __tablename__ = "gateway_settlement_schedules"
    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(Integer, ForeignKey("payment_gateway_connections.id"), nullable=False)
    settlement_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String, default="pending")
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class PendingJournalEntry(Base):
    """Maker-Checker: pending journal entries awaiting second approval."""
    __tablename__ = "pending_journal_entries"
    __table_args__ = (Index("ix_pending_je_status", "status"), Index("ix_pending_je_maker", "created_by"), Index("ix_pending_je_country", "country_code"))

    id = Column(Integer, primary_key=True, index=True)
    lines_json = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    country_code = Column(String(10), nullable=True)
    entry_date = Column(DateTime, nullable=False)
    amount_threshold_triggered = Column(Boolean, default=False)
    status = Column(String(20), default="pending_approval")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class PayoutBatch(Base):
    """Payout batch for supplier/logistics payouts with state machine."""
    __tablename__ = "payout_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(50), unique=True, nullable=False)
    country_code = Column(String(10), nullable=False, index=True)
    total_amount = Column(Numeric(16, 4), default=0)
    item_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    items = relationship("PayoutBatchItem", back_populates="batch", cascade="all, delete-orphan")


class PayoutBatchItem(Base):
    __tablename__ = "payout_batch_items"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("payout_batches.id"), nullable=False)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    amount = Column(Numeric(16, 4), nullable=False)
    currency = Column(String(3), default="USD")
    reference = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    country_code = Column(String(10), nullable=True, index=True)

    batch = relationship("PayoutBatch", back_populates="items")


class BankMappingRule(Base):
    """Configurable mapping: bank-statement description pattern -> GL account + side."""
    __tablename__ = "bank_mapping_rules"
    __table_args__ = (
        Index("ix_bank_mapping_country", "country_code"),
        Index("ix_bank_mapping_priority", "priority"),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    # Keywords matched (case-insensitive) against the statement description.
    match_pattern = Column(String(300), nullable=False)
    description_contains = Column(String(300), nullable=True)
    account_code = Column(String(20), nullable=False)
    normal_side = Column(String(10), nullable=False)  # debit / credit
    category = Column(String(40), nullable=True)
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class BankStatementImport(Base):
    """Header record for one uploaded bank statement file."""
    __tablename__ = "bank_statement_imports"
    __table_args__ = (Index("ix_bsi_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(120), nullable=True)
    file_name = Column(String(255), nullable=True)
    statement_period_start = Column(DateTime, nullable=True)
    statement_period_end = Column(DateTime, nullable=True)
    currency = Column(String(3), default="OMR")
    total_lines = Column(Integer, default=0)
    matched_lines = Column(Integer, default=0)
    unmatched_lines = Column(Integer, default=0)
    status = Column(String(20), default="imported")
    imported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class BankStatementLine(Base):
    """A single line from an imported bank statement awaiting mapping/reconciliation."""
    __tablename__ = "bank_statement_lines"
    __table_args__ = (
        Index("ix_bsl_import", "import_id"),
        Index("ix_bsl_status", "status"),
        Index("ix_bsl_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(Integer, ForeignKey("bank_statement_imports.id"), nullable=False, index=True)
    txn_date = Column(DateTime, nullable=True)
    description = Column(String(500), nullable=True)
    reference = Column(String(120), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    # Resolved GL account_code (set when matched by a BankMappingRule).
    mapped_account_code = Column(String(20), nullable=True)
    mapped_side = Column(String(10), nullable=True)
    mapping_rule_id = Column(Integer, ForeignKey("bank_mapping_rules.id"), nullable=True)
    status = Column(String(20), default="unmapped")  # unmapped, mapped, posted, reconciled
    posted_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    reconciled_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class FixedAsset(Base):
    """Fixed asset register with straight-line depreciation schedule."""
    __tablename__ = "fixed_assets"
    __table_args__ = (Index("ix_fa_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    asset_code = Column(String(40), nullable=True)
    category = Column(String(40), nullable=True)
    purchase_date = Column(DateTime, nullable=False)
    purchase_cost = Column(Numeric(14, 2), nullable=False)
    salvage_value = Column(Numeric(14, 2), default=0)
    useful_life_months = Column(Integer, nullable=False)
    accumulated_depreciation = Column(Numeric(14, 2), default=0)
    last_depreciated_date = Column(DateTime, nullable=True)
    asset_account_code = Column(String(20), default="1100")
    depreciation_account_code = Column(String(20), default="5070")
    accumulated_depr_account_code = Column(String(20), default="1190")
    status = Column(String(20), default="active")  # active, disposed, fully_depreciated
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Accrual(Base):
    """Accrued expense / revenue recognized before cash movement."""
    __tablename__ = "accruals"
    __table_args__ = (Index("ix_accrual_country", "country_code"), Index("ix_accrual_status", "status"))
    id = Column(Integer, primary_key=True, index=True)
    accrual_type = Column(String(20), nullable=False)  # expense / revenue
    description = Column(String(500), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    expense_account_code = Column(String(20), nullable=False)
    accrual_account_code = Column(String(20), nullable=False)
    accrual_date = Column(DateTime, nullable=False)
    reversal_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="open")  # open, reversed, cleared
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    reversal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ScannedExpense(Base):
    """Bill scanned via OCR that becomes an expense + GL posting after approval."""
    __tablename__ = "scanned_expenses"
    __table_args__ = (Index("ix_se_country", "country_code"), Index("ix_se_status", "status"))
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    vendor_name = Column(String(200), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    expense_date = Column(DateTime, nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="OMR")
    tax_amount = Column(Numeric(14, 2), default=0)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    expense_account_code = Column(String(20), nullable=True)
    image_url = Column(String(500), nullable=True)
    ocr_raw_text = Column(Text, nullable=True)
    ocr_confidence = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), default="scanned")  # scanned, reviewed, posted, rejected
    posted_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Vendor(Base):
    """Vendor master (entity we receive bills from / owe money to)."""
    __tablename__ = "vendors"
    __table_args__ = (Index("ix_vendors_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(60), nullable=True)
    contact_email = Column(String(160), nullable=True)
    currency = Column(String(3), default="OMR")
    payment_terms_days = Column(Integer, default=30)
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Customer(Base):
    """Customer master for B2B / trade receivables (distinct from platform User)."""
    __tablename__ = "customers"
    __table_args__ = (Index("ix_customers_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(60), nullable=True)
    contact_email = Column(String(160), nullable=True)
    currency = Column(String(3), default="OMR")
    payment_terms_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(14, 2), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CostCenter(Base):
    """Cost center / department used to tag journal lines for reporting."""
    __tablename__ = "cost_centers"
    __table_args__ = (Index("ix_cost_centers_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), nullable=False)
    name = Column(String(160), nullable=False)
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class APBill(Base):
    """Accounts-Payable bill received from a vendor (dr expense/asset, cr AP)."""
    __tablename__ = "ap_bills"
    __table_args__ = (
        Index("ix_ap_bills_vendor", "vendor_id"),
        Index("ix_ap_bills_status", "status"),
        Index("ix_ap_bills_due", "due_date"),
        Index("ix_ap_bills_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    bill_number = Column(String(80), nullable=True)
    bill_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    account_code = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=0)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="received")  # received, approved, paid, cancelled
    linked_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    paid_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    vendor = relationship("Vendor", foreign_keys=[vendor_id])


class ARInvoice(Base):
    """Accounts-Receivable invoice issued to a customer (dr AR, cr Revenue)."""
    __tablename__ = "ar_invoices"
    __table_args__ = (
        Index("ix_ar_invoices_customer", "customer_id"),
        Index("ix_ar_invoices_status", "status"),
        Index("ix_ar_invoices_due", "due_date"),
        Index("ix_ar_invoices_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    invoice_number = Column(String(80), nullable=True)
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=True)
    account_code = Column(String(20), default="4010")
    amount = Column(Numeric(14, 2), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=0)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="issued")  # issued, partially_paid, paid, written_off
    linked_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    paid_journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    customer = relationship("Customer", foreign_keys=[customer_id])


class BankAccount(Base):
    """Company bank-account registry mapped to a GL cash account."""
    __tablename__ = "bank_accounts"
    __table_args__ = (Index("ix_bank_accounts_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(160), nullable=False)
    account_name = Column(String(200), nullable=True)
    account_number = Column(String(60), nullable=True)
    iban = Column(String(60), nullable=True)
    swift_bic = Column(String(20), nullable=True)
    currency = Column(String(3), default="OMR")
    gl_account_code = Column(String(20), default="1010")
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Budget(Base):
    """Period budget per GL account for variance reporting."""
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("account_code", "fiscal_period_id", "country_code", name="uq_budget_account_period"),
        Index("ix_budgets_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    account_code = Column(String(20), nullable=False)
    fiscal_period_id = Column(Integer, ForeignKey("fiscal_periods.id"), nullable=False)
    amount = Column(Numeric(16, 4), nullable=False)
    currency = Column(String(3), default="OMR")
    country_code = Column(String(10), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    period = relationship("FiscalPeriod", foreign_keys=[fiscal_period_id])


class BankReconciliation(Base):
    """Human-reviewed match between a bank statement line and a GL journal entry."""
    __tablename__ = "bank_reconciliations"
    __table_args__ = (
        UniqueConstraint("statement_line_id", name="uq_bank_recon_line"),
        Index("ix_bank_recon_status", "status"),
        Index("ix_bank_recon_country", "country_code"),
    )
    id = Column(Integer, primary_key=True, index=True)
    statement_line_id = Column(Integer, ForeignKey("bank_statement_lines.id"), nullable=False, index=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    matched_amount = Column(Numeric(14, 2), nullable=True)
    status = Column(String(20), default="matched")  # matched, post_and_matched, broken
    note = Column(Text, nullable=True)
    matched_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    matched_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    statement_line = relationship("BankStatementLine", foreign_keys=[statement_line_id])


class RecurringTemplate(Base):
    """Template that generates a journal entry on trigger (e.g. monthly rent)."""
    __tablename__ = "recurring_templates"
    __table_args__ = (Index("ix_recurring_country", "country_code"),)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    frequency = Column(String(20), default="monthly")  # daily, weekly, monthly, quarterly, yearly
    next_run_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    lines = Column(JSON, nullable=False)  # list of {account_code, side, amount, description}
    currency = Column(String(3), default="OMR")
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class FinanceAuditLog(Base):
    """Scoped audit trail of finance actions (posts, reversals, approvals, automations)."""
    __tablename__ = "finance_audit_logs"
    __table_args__ = (
        Index("ix_finance_audit_action", "action"),
        Index("ix_finance_audit_actor", "actor_id"),
        Index("ix_finance_audit_at", "created_at"),
    )
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(60), nullable=False)  # journal_post, journal_reverse, approval, reconciliation, automation
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role = Column(String(40), nullable=True)
    entity_type = Column(String(40), nullable=True)
    entity_id = Column(Integer, nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class FinanceAutomationLog(Base):
    """Audit trail for automation runs (OCR, reconciliation, depreciation, mapping)."""
    __tablename__ = "finance_automation_logs"
    __table_args__ = (Index("ix_fal_kind", "kind"), Index("ix_fal_country", "country_code"))
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(40), nullable=False)  # ocr_scan, bank_reconcile, depreciation, mapping
    records_processed = Column(Integer, default=0)
    records_changed = Column(Integer, default=0)
    detail = Column(JSON, nullable=True)
    run_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

