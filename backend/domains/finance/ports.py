"""finance domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.finance.models`` or ``domains.finance.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items



# Lazy model imports to break circular dependencies
@lru_cache(maxsize=128)
def _get_model(name):
    import importlib
    model_map = {
        'CommissionAgreement': 'domains.finance.models.commission',
        'CommissionCategoryRate': 'domains.finance.models.commission',
        'CommissionLedgerEntry': 'domains.finance.models.commission',
        'ProductCommissionOverride': 'domains.finance.models.commission',
        'CustomsEntry': 'domains.finance.models.erp',
        'GoodsReceiptLine': 'domains.finance.models.erp',
        'GoodsReceiptNote': 'domains.finance.models.erp',
        'ImportCostTemplate': 'domains.finance.models.erp',
        'ImportShipment': 'domains.finance.models.erp',
        'ImportShipmentLine': 'domains.finance.models.erp',
        'LandedCostAllocation': 'domains.finance.models.erp',
        'PurchaseOrder': 'domains.finance.models.erp',
        'PurchaseOrderLine': 'domains.finance.models.erp',
        'SalesOrder': 'domains.finance.models.erp',
        'SalesOrderLine': 'domains.finance.models.erp',
        'StockMovement': 'domains.finance.models.erp',
        'Warehouse': 'domains.finance.models.erp',
    }
    if name in model_map:
        mod = importlib.import_module(model_map[name])
        return getattr(mod, name)
    mod = importlib.import_module('domains.finance.models.general_ledger')
    return getattr(mod, name)




def get_warehouse_by_id(db: Session, id_: int) -> Optional[Warehouse]:
    """Return Warehouse by primary key (or None)."""
    return db.get(Warehouse, id_)

def list_warehouses(db: Session, limit: int = 100) -> List[Warehouse]:
    """Return up to ``limit`` Warehouse rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Warehouse, db, limit)


def get_purchase_order_by_id(db: Session, id_: int) -> Optional[PurchaseOrder]:
    """Return PurchaseOrder by primary key (or None)."""
    return db.get(PurchaseOrder, id_)

def list_purchase_orders(db: Session, limit: int = 100) -> List[PurchaseOrder]:
    """Return up to ``limit`` PurchaseOrder rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PurchaseOrder, db, limit)


def get_purchase_order_line_by_id(db: Session, id_: int) -> Optional[PurchaseOrderLine]:
    """Return PurchaseOrderLine by primary key (or None)."""
    return db.get(PurchaseOrderLine, id_)

def list_purchase_order_lines(db: Session, limit: int = 100) -> List[PurchaseOrderLine]:
    """Return up to ``limit`` PurchaseOrderLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PurchaseOrderLine, db, limit)


def get_goods_receipt_note_by_id(db: Session, id_: int) -> Optional[GoodsReceiptNote]:
    """Return GoodsReceiptNote by primary key (or None)."""
    return db.get(GoodsReceiptNote, id_)

def list_goods_receipt_notes(db: Session, limit: int = 100) -> List[GoodsReceiptNote]:
    """Return up to ``limit`` GoodsReceiptNote rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GoodsReceiptNote, db, limit)


def get_goods_receipt_line_by_id(db: Session, id_: int) -> Optional[GoodsReceiptLine]:
    """Return GoodsReceiptLine by primary key (or None)."""
    return db.get(GoodsReceiptLine, id_)

def list_goods_receipt_lines(db: Session, limit: int = 100) -> List[GoodsReceiptLine]:
    """Return up to ``limit`` GoodsReceiptLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GoodsReceiptLine, db, limit)


def get_sales_order_by_id(db: Session, id_: int) -> Optional[SalesOrder]:
    """Return SalesOrder by primary key (or None)."""
    return db.get(SalesOrder, id_)

def list_sales_orders(db: Session, limit: int = 100) -> List[SalesOrder]:
    """Return up to ``limit`` SalesOrder rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SalesOrder, db, limit)


def get_sales_order_line_by_id(db: Session, id_: int) -> Optional[SalesOrderLine]:
    """Return SalesOrderLine by primary key (or None)."""
    return db.get(SalesOrderLine, id_)

def list_sales_order_lines(db: Session, limit: int = 100) -> List[SalesOrderLine]:
    """Return up to ``limit`` SalesOrderLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SalesOrderLine, db, limit)


def get_stock_movement_by_id(db: Session, id_: int) -> Optional[StockMovement]:
    """Return StockMovement by primary key (or None)."""
    return db.get(StockMovement, id_)

def list_stock_movements(db: Session, limit: int = 100) -> List[StockMovement]:
    """Return up to ``limit`` StockMovement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(StockMovement, db, limit)


def get_import_shipment_by_id(db: Session, id_: int) -> Optional[ImportShipment]:
    """Return ImportShipment by primary key (or None)."""
    return db.get(ImportShipment, id_)

def list_import_shipments(db: Session, limit: int = 100) -> List[ImportShipment]:
    """Return up to ``limit`` ImportShipment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportShipment, db, limit)


def get_import_shipment_line_by_id(db: Session, id_: int) -> Optional[ImportShipmentLine]:
    """Return ImportShipmentLine by primary key (or None)."""
    return db.get(ImportShipmentLine, id_)

def list_import_shipment_lines(db: Session, limit: int = 100) -> List[ImportShipmentLine]:
    """Return up to ``limit`` ImportShipmentLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportShipmentLine, db, limit)


def get_landed_cost_allocation_by_id(db: Session, id_: int) -> Optional[LandedCostAllocation]:
    """Return LandedCostAllocation by primary key (or None)."""
    return db.get(LandedCostAllocation, id_)

def list_landed_cost_allocations(db: Session, limit: int = 100) -> List[LandedCostAllocation]:
    """Return up to ``limit`` LandedCostAllocation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LandedCostAllocation, db, limit)


def get_customs_entry_by_id(db: Session, id_: int) -> Optional[CustomsEntry]:
    """Return CustomsEntry by primary key (or None)."""
    return db.get(CustomsEntry, id_)

def list_customs_entries(db: Session, limit: int = 100) -> List[CustomsEntry]:
    """Return up to ``limit`` CustomsEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CustomsEntry, db, limit)


def get_import_cost_template_by_id(db: Session, id_: int) -> Optional[ImportCostTemplate]:
    """Return ImportCostTemplate by primary key (or None)."""
    return db.get(ImportCostTemplate, id_)

def list_import_cost_templates(db: Session, limit: int = 100) -> List[ImportCostTemplate]:
    """Return up to ``limit`` ImportCostTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportCostTemplate, db, limit)


def get_fiscal_period_by_id(db: Session, id_: int) -> Optional[FiscalPeriod]:
    """Return FiscalPeriod by primary key (or None)."""
    return db.get(FiscalPeriod, id_)

def list_fiscal_periods(db: Session, limit: int = 100) -> List[FiscalPeriod]:
    """Return up to ``limit`` FiscalPeriod rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FiscalPeriod, db, limit)


def get_transaction_ledger_by_id(db: Session, id_: int) -> Optional[TransactionLedger]:
    """Return TransactionLedger by primary key (or None)."""
    return db.get(TransactionLedger, id_)

def list_transaction_ledgers(db: Session, limit: int = 100) -> List[TransactionLedger]:
    """Return up to ``limit`` TransactionLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TransactionLedger, db, limit)


def get_supplier_settlement_by_id(db: Session, id_: int) -> Optional[SupplierSettlement]:
    """Return SupplierSettlement by primary key (or None)."""
    return db.get(SupplierSettlement, id_)

def list_supplier_settlements(db: Session, limit: int = 100) -> List[SupplierSettlement]:
    """Return up to ``limit`` SupplierSettlement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierSettlement, db, limit)


def get_journal_entry_by_id(db: Session, id_: int) -> Optional[JournalEntry]:
    """Return JournalEntry by primary key (or None)."""
    return db.get(JournalEntry, id_)

def list_journal_entries(db: Session, limit: int = 100) -> List[JournalEntry]:
    """Return up to ``limit`` JournalEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(JournalEntry, db, limit)


def get_journal_entry_line_by_id(db: Session, id_: int) -> Optional[JournalEntryLine]:
    """Return JournalEntryLine by primary key (or None)."""
    return db.get(JournalEntryLine, id_)

def list_journal_entry_lines(db: Session, limit: int = 100) -> List[JournalEntryLine]:
    """Return up to ``limit`` JournalEntryLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(JournalEntryLine, db, limit)


def get_account_by_id(db: Session, id_: int) -> Optional[Account]:
    """Return Account by primary key (or None)."""
    return db.get(Account, id_)

def list_accounts(db: Session, limit: int = 100) -> List[Account]:
    """Return up to ``limit`` Account rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Account, db, limit)


def get_account_group_by_id(db: Session, id_: int) -> Optional[AccountGroup]:
    """Return AccountGroup by primary key (or None)."""
    return db.get(AccountGroup, id_)

def list_account_groups(db: Session, limit: int = 100) -> List[AccountGroup]:
    """Return up to ``limit`` AccountGroup rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AccountGroup, db, limit)


def get_account_balance_by_id(db: Session, id_: int) -> Optional[AccountBalance]:
    """Return AccountBalance by primary key (or None)."""
    return db.get(AccountBalance, id_)

def list_account_balances(db: Session, limit: int = 100) -> List[AccountBalance]:
    """Return up to ``limit`` AccountBalance rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AccountBalance, db, limit)


def get_a_r_ledger_entry_by_id(db: Session, id_: int) -> Optional[ARLedgerEntry]:
    """Return ARLedgerEntry by primary key (or None)."""
    return db.get(ARLedgerEntry, id_)

def list_ar_ledger_entries(db: Session, limit: int = 100) -> List[ARLedgerEntry]:
    """Return up to ``limit`` ARLedgerEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ARLedgerEntry, db, limit)


def get_a_p_ledger_by_id(db: Session, id_: int) -> Optional[APLedger]:
    """Return APLedger by primary key (or None)."""
    return db.get(APLedger, id_)

def list_ap_ledgers(db: Session, limit: int = 100) -> List[APLedger]:
    """Return up to ``limit`` APLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(APLedger, db, limit)



def get_invoice_by_id(db: Session, id_: int) -> Optional[Invoice]:
    """Return Invoice by primary key (or None)."""
    return db.get(Invoice, id_)

def list_invoices(db: Session, limit: int = 100) -> List[Invoice]:
    """Return up to ``limit`` Invoice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Invoice, db, limit)


def get_invoice_item_by_id(db: Session, id_: int) -> Optional[InvoiceItem]:
    """Return InvoiceItem by primary key (or None)."""
    return db.get(InvoiceItem, id_)

def list_invoice_items(db: Session, limit: int = 100) -> List[InvoiceItem]:
    """Return up to ``limit`` InvoiceItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InvoiceItem, db, limit)


def get_refund_ledger_by_id(db: Session, id_: int) -> Optional[RefundLedger]:
    """Return RefundLedger by primary key (or None)."""
    return db.get(RefundLedger, id_)

def list_refund_ledgers(db: Session, limit: int = 100) -> List[RefundLedger]:
    """Return up to ``limit`` RefundLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RefundLedger, db, limit)


def get_bank_transaction_by_id(db: Session, id_: int) -> Optional[BankTransaction]:
    """Return BankTransaction by primary key (or None)."""
    return db.get(BankTransaction, id_)

def list_bank_transactions(db: Session, limit: int = 100) -> List[BankTransaction]:
    """Return up to ``limit`` BankTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankTransaction, db, limit)


def get_v_a_t_remittance_by_id(db: Session, id_: int) -> Optional[VATRemittance]:
    """Return VATRemittance by primary key (or None)."""
    return db.get(VATRemittance, id_)

def list_vat_remittances(db: Session, limit: int = 100) -> List[VATRemittance]:
    """Return up to ``limit`` VATRemittance rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VATRemittance, db, limit)


def get_cash_account_by_id(db: Session, id_: int) -> Optional[CashAccount]:
    """Return CashAccount by primary key (or None)."""
    return db.get(CashAccount, id_)

def list_cash_accounts(db: Session, limit: int = 100) -> List[CashAccount]:
    """Return up to ``limit`` CashAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashAccount, db, limit)


def get_cash_transaction_by_id(db: Session, id_: int) -> Optional[CashTransaction]:
    """Return CashTransaction by primary key (or None)."""
    return db.get(CashTransaction, id_)

def list_cash_transactions(db: Session, limit: int = 100) -> List[CashTransaction]:
    """Return up to ``limit`` CashTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashTransaction, db, limit)


def get_treasury_account_by_id(db: Session, id_: int) -> Optional[TreasuryAccount]:
    """Return TreasuryAccount by primary key (or None)."""
    return db.get(TreasuryAccount, id_)

def list_treasury_accounts(db: Session, limit: int = 100) -> List[TreasuryAccount]:
    """Return up to ``limit`` TreasuryAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TreasuryAccount, db, limit)


def get_treasury_transaction_by_id(db: Session, id_: int) -> Optional[TreasuryTransaction]:
    """Return TreasuryTransaction by primary key (or None)."""
    return db.get(TreasuryTransaction, id_)

def list_treasury_transactions(db: Session, limit: int = 100) -> List[TreasuryTransaction]:
    """Return up to ``limit`` TreasuryTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TreasuryTransaction, db, limit)


def get_cash_flow_forecast_by_id(db: Session, id_: int) -> Optional[CashFlowForecast]:
    """Return CashFlowForecast by primary key (or None)."""
    return db.get(CashFlowForecast, id_)

def list_cash_flow_forecasts(db: Session, limit: int = 100) -> List[CashFlowForecast]:
    """Return up to ``limit`` CashFlowForecast rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashFlowForecast, db, limit)


def get_cash_position_snapshot_by_id(db: Session, id_: int) -> Optional[CashPositionSnapshot]:
    """Return CashPositionSnapshot by primary key (or None)."""
    return db.get(CashPositionSnapshot, id_)

def list_cash_position_snapshots(db: Session, limit: int = 100) -> List[CashPositionSnapshot]:
    """Return up to ``limit`` CashPositionSnapshot rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashPositionSnapshot, db, limit)


def get_gateway_settlement_schedule_by_id(db: Session, id_: int) -> Optional[GatewaySettlementSchedule]:
    """Return GatewaySettlementSchedule by primary key (or None)."""
    return db.get(GatewaySettlementSchedule, id_)

def list_gateway_settlement_schedules(db: Session, limit: int = 100) -> List[GatewaySettlementSchedule]:
    """Return up to ``limit`` GatewaySettlementSchedule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GatewaySettlementSchedule, db, limit)


def get_pending_journal_entry_by_id(db: Session, id_: int) -> Optional[PendingJournalEntry]:
    """Return PendingJournalEntry by primary key (or None)."""
    return db.get(PendingJournalEntry, id_)

def list_pending_journal_entries(db: Session, limit: int = 100) -> List[PendingJournalEntry]:
    """Return up to ``limit`` PendingJournalEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PendingJournalEntry, db, limit)


def get_payout_batch_by_id(db: Session, id_: int) -> Optional[PayoutBatch]:
    """Return PayoutBatch by primary key (or None)."""
    return db.get(PayoutBatch, id_)

def list_payout_batches(db: Session, limit: int = 100) -> List[PayoutBatch]:
    """Return up to ``limit`` PayoutBatch rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PayoutBatch, db, limit)


def get_payout_batch_item_by_id(db: Session, id_: int) -> Optional[PayoutBatchItem]:
    """Return PayoutBatchItem by primary key (or None)."""
    return db.get(PayoutBatchItem, id_)

def list_payout_batch_items(db: Session, limit: int = 100) -> List[PayoutBatchItem]:
    """Return up to ``limit`` PayoutBatchItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PayoutBatchItem, db, limit)


def get_bank_mapping_rule_by_id(db: Session, id_: int) -> Optional[BankMappingRule]:
    """Return BankMappingRule by primary key (or None)."""
    return db.get(BankMappingRule, id_)

def list_bank_mapping_rules(db: Session, limit: int = 100) -> List[BankMappingRule]:
    """Return up to ``limit`` BankMappingRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankMappingRule, db, limit)


def get_bank_statement_import_by_id(db: Session, id_: int) -> Optional[BankStatementImport]:
    """Return BankStatementImport by primary key (or None)."""
    return db.get(BankStatementImport, id_)

def list_bank_statement_imports(db: Session, limit: int = 100) -> List[BankStatementImport]:
    """Return up to ``limit`` BankStatementImport rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankStatementImport, db, limit)


def get_bank_statement_line_by_id(db: Session, id_: int) -> Optional[BankStatementLine]:
    """Return BankStatementLine by primary key (or None)."""
    return db.get(BankStatementLine, id_)

def list_bank_statement_lines(db: Session, limit: int = 100) -> List[BankStatementLine]:
    """Return up to ``limit`` BankStatementLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankStatementLine, db, limit)


def get_fixed_asset_by_id(db: Session, id_: int) -> Optional[FixedAsset]:
    """Return FixedAsset by primary key (or None)."""
    return db.get(FixedAsset, id_)

def list_fixed_assets(db: Session, limit: int = 100) -> List[FixedAsset]:
    """Return up to ``limit`` FixedAsset rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FixedAsset, db, limit)


def get_accrual_by_id(db: Session, id_: int) -> Optional[Accrual]:
    """Return Accrual by primary key (or None)."""
    return db.get(Accrual, id_)

def list_accruals(db: Session, limit: int = 100) -> List[Accrual]:
    """Return up to ``limit`` Accrual rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Accrual, db, limit)


def get_scanned_expense_by_id(db: Session, id_: int) -> Optional[ScannedExpense]:
    """Return ScannedExpense by primary key (or None)."""
    return db.get(ScannedExpense, id_)

def list_scanned_expenses(db: Session, limit: int = 100) -> List[ScannedExpense]:
    """Return up to ``limit`` ScannedExpense rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ScannedExpense, db, limit)


def get_vendor_by_id(db: Session, id_: int) -> Optional[Vendor]:
    """Return Vendor by primary key (or None)."""
    return db.get(Vendor, id_)

def list_vendors(db: Session, limit: int = 100) -> List[Vendor]:
    """Return up to ``limit`` Vendor rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Vendor, db, limit)


def get_customer_by_id(db: Session, id_: int) -> Optional[Customer]:
    """Return Customer by primary key (or None)."""
    return db.get(Customer, id_)

def list_customers(db: Session, limit: int = 100) -> List[Customer]:
    """Return up to ``limit`` Customer rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Customer, db, limit)


def get_cost_center_by_id(db: Session, id_: int) -> Optional[CostCenter]:
    """Return CostCenter by primary key (or None)."""
    return db.get(CostCenter, id_)

def list_cost_centers(db: Session, limit: int = 100) -> List[CostCenter]:
    """Return up to ``limit`` CostCenter rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CostCenter, db, limit)


def get_a_p_bill_by_id(db: Session, id_: int) -> Optional[APBill]:
    """Return APBill by primary key (or None)."""
    return db.get(APBill, id_)

def list_ap_bills(db: Session, limit: int = 100) -> List[APBill]:
    """Return up to ``limit`` APBill rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(APBill, db, limit)


def get_a_r_invoice_by_id(db: Session, id_: int) -> Optional[ARInvoice]:
    """Return ARInvoice by primary key (or None)."""
    return db.get(ARInvoice, id_)

def list_ar_invoices(db: Session, limit: int = 100) -> List[ARInvoice]:
    """Return up to ``limit`` ARInvoice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ARInvoice, db, limit)


def get_bank_account_by_id(db: Session, id_: int) -> Optional[BankAccount]:
    """Return BankAccount by primary key (or None)."""
    return db.get(BankAccount, id_)

def list_bank_accounts(db: Session, limit: int = 100) -> List[BankAccount]:
    """Return up to ``limit`` BankAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankAccount, db, limit)


def get_budget_by_id(db: Session, id_: int) -> Optional[Budget]:
    """Return Budget by primary key (or None)."""
    return db.get(Budget, id_)

def list_budgets(db: Session, limit: int = 100) -> List[Budget]:
    """Return up to ``limit`` Budget rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Budget, db, limit)


def get_bank_reconciliation_by_id(db: Session, id_: int) -> Optional[BankReconciliation]:
    """Return BankReconciliation by primary key (or None)."""
    return db.get(BankReconciliation, id_)

def list_bank_reconciliations(db: Session, limit: int = 100) -> List[BankReconciliation]:
    """Return up to ``limit`` BankReconciliation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankReconciliation, db, limit)


def get_recurring_template_by_id(db: Session, id_: int) -> Optional[RecurringTemplate]:
    """Return RecurringTemplate by primary key (or None)."""
    return db.get(RecurringTemplate, id_)

def list_recurring_templates(db: Session, limit: int = 100) -> List[RecurringTemplate]:
    """Return up to ``limit`` RecurringTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RecurringTemplate, db, limit)


def get_finance_audit_log_by_id(db: Session, id_: int) -> Optional[FinanceAuditLog]:
    """Return FinanceAuditLog by primary key (or None)."""
    return db.get(FinanceAuditLog, id_)

def list_finance_audit_logs(db: Session, limit: int = 100) -> List[FinanceAuditLog]:
    """Return up to ``limit`` FinanceAuditLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FinanceAuditLog, db, limit)


def get_finance_automation_log_by_id(db: Session, id_: int) -> Optional[FinanceAutomationLog]:
    """Return FinanceAutomationLog by primary key (or None)."""
    return db.get(FinanceAutomationLog, id_)

def list_finance_automation_logs(db: Session, limit: int = 100) -> List[FinanceAutomationLog]:
    """Return up to ``limit`` FinanceAutomationLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FinanceAutomationLog, db, limit)


def get_automation_rule_by_id(db: Session, id_: int) -> Optional[AutomationRule]:
    """Return AutomationRule by primary key (or None)."""
    return db.get(AutomationRule, id_)

def list_automation_rules(db: Session, limit: int = 100) -> List[AutomationRule]:
    """Return up to ``limit`` AutomationRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AutomationRule, db, limit)


def get_automation_log_by_id(db: Session, id_: int) -> Optional[AutomationLog]:
    """Return AutomationLog by primary key (or None)."""
    return db.get(AutomationLog, id_)

def list_automation_logs(db: Session, limit: int = 100) -> List[AutomationLog]:
    """Return up to ``limit`` AutomationLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AutomationLog, db, limit)



# --- Query delegation (Law 3 sanctioned cross-domain query surface) ---

def journal_entry_query(db: Session) -> object:
    """Return a base ``JournalEntry`` query for sanctioned cross-domain delegation."""
    return db.query(JournalEntry)


def journal_entry_model() -> type:
    """Return the ``JournalEntry`` model class (for column reference only)."""
    return JournalEntry

# --- P11 re-exports (Law 3 sanctioned read/behavior surface) ---
from domains.finance.models.finance import *
from domains.finance.services.ledger.general_ledger import post_logistics_cod_remittance_journal, post_supplier_settlement_journal
from domains.finance.services.ledger.je_reversal_service import reverse_journal_entry

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "commission_engine": ("domains.finance.services.finance_service", "commission_engine"),
    "create_invoice_from_order": ("domains.finance.services.ledger.invoice_service", "create_invoice_from_order"),
    "_apply_stripe_runtime_key": ("domains.finance.services.payments.payment_engine", "_apply_stripe_runtime_key"),
    "apply_order_status_change": ("domains.finance.services.payments.payment_engine", "apply_order_status_change"),
    "_order_holds_inventory": ("domains.finance.services.payments.payment_engine", "_order_holds_inventory"),
    "remove_background": ("domains.finance.services.shared.bg_removal_service", "remove_background"),
    "confirm_purchase_order": ("domains.finance.services.trading_service", "confirm_purchase_order"),
    "confirm_sales_order": ("domains.finance.services.trading_service", "confirm_sales_order"),
    "create_purchase_order": ("domains.finance.services.trading_service", "create_purchase_order"),
    "create_sales_order": ("domains.finance.services.trading_service", "create_sales_order"),
    "create_warehouse": ("domains.finance.services.trading_service", "create_warehouse"),
    "dispatch_sales_order": ("domains.finance.services.trading_service", "dispatch_sales_order"),
    "get_goods_receipt": ("domains.finance.services.trading_service", "get_goods_receipt"),
    "get_purchase_order": ("domains.finance.services.trading_service", "get_purchase_order"),
    "get_sales_order": ("domains.finance.services.trading_service", "get_sales_order"),
    "get_stock_level": ("domains.finance.services.trading_service", "get_stock_level"),
    "invoice_sales_order": ("domains.finance.services.trading_service", "invoice_sales_order"),
    "list_goods_receipts": ("domains.finance.services.trading_service", "list_goods_receipts"),
    "list_purchase_orders": ("domains.finance.services.trading_service", "list_purchase_orders"),
    "list_sales_orders": ("domains.finance.services.trading_service", "list_sales_orders"),
    "list_stock_movements": ("domains.finance.services.trading_service", "list_stock_movements"),
    "list_warehouses": ("domains.finance.services.trading_service", "list_warehouses"),
    "receive_purchase_order": ("domains.finance.services.trading_service", "receive_purchase_order"),
    "run_dunning_engine": ("domains.finance.services.trading_service", "run_dunning_engine"),
    "three_way_match": ("domains.finance.services.trading_service", "three_way_match"),
    "run_scheduled_finance_cycle": ("domains.finance.services.treasury.cash_management_service", "run_scheduled_finance_cycle"),
    "run_scheduled_reconciliation_cycle": ("domains.finance.services.treasury.cash_management_service", "run_scheduled_reconciliation_cycle"),
    "apply_shipment_vehicle_selection": ("domains.finance.services.treasury.cash_management_service", "apply_shipment_vehicle_selection"),
    "create_cod_remittance_receipt": ("domains.finance.services.treasury.cash_management_service", "create_cod_remittance_receipt"),
    "create_settlements_on_delivery": ("domains.finance.services.treasury.cash_management_service", "create_settlements_on_delivery"),
    "deserialize_pricing_breakdown_json": ("domains.finance.services.treasury.cash_management_service", "deserialize_pricing_breakdown_json"),
    "effective_allocation_delivery_amounts": ("domains.finance.services.treasury.cash_management_service", "effective_allocation_delivery_amounts"),
    "list_cod_remittance_receipts": ("domains.finance.services.treasury.cash_management_service", "list_cod_remittance_receipts"),
    "serialize_cod_remittance_receipt": ("domains.finance.services.treasury.cash_management_service", "serialize_cod_remittance_receipt"),
    "log_refund_bank_transaction": ("domains.finance.services.treasury.cash_management_service", "log_refund_bank_transaction"),
    "log_bank_transaction": ("domains.finance.services.treasury.cash_management_service", "log_bank_transaction"),
    "create_cash_account": ("domains.finance.services.treasury.cash_write_service", "create_cash_account"),
    "create_cash_transaction": ("domains.finance.services.treasury.cash_write_service", "create_cash_transaction"),
    "TreasuryService": ("domains.finance.services.treasury.treasury_service", "TreasuryService"),
    "controller_get_ap_summary": ("domains.finance.services.ledger.accounting_controller", "controller_get_ap_summary"),
    "FinancialReportingService": ("domains.finance.services.ledger.accounting_controller", "FinancialReportingService"),
    "get_or_create_fiscal_period": ("domains.finance.services.ledger.accounting_controller", "get_or_create_fiscal_period"),
    "get_current_fiscal_period": ("domains.finance.services.ledger.accounting_controller", "get_current_fiscal_period"),
    "close_period": ("domains.finance.services.ledger.accounting_controller", "close_period"),
    "controller_get_ar_summary": ("domains.finance.services.ledger.accounting_controller", "controller_get_ar_summary"),
    "controller_post_ar_invoice": ("domains.finance.services.ledger.accounting_controller", "controller_post_ar_invoice"),
    "controller_post_ar_payment": ("domains.finance.services.ledger.accounting_controller", "controller_post_ar_payment"),
    "controller_post_ap_payable": ("domains.finance.services.ledger.accounting_controller", "controller_post_ap_payable"),
    "controller_post_ap_payment": ("domains.finance.services.ledger.accounting_controller", "controller_post_ap_payment"),
    "list_pending_payouts": ("domains.finance.services.payouts.payout_batch_service", "list_pending_payouts"),
    "approve_payout": ("domains.finance.services.payouts.payout_batch_service", "approve_payout"),
    "reject_payout": ("domains.finance.services.payouts.payout_batch_service", "reject_payout"),
    "approve_batch": ("domains.finance.services.payouts.payout_batch_service", "approve_batch"),
    "reject_batch": ("domains.finance.services.payouts.payout_batch_service", "reject_batch"),
    "dispatch_batch": ("domains.finance.services.payouts.payout_batch_service", "dispatch_batch"),
    "get_background_job_status": ("domains.finance.services.payouts.payout_batch_service", "get_background_job_status"),
    "start_auto_payout_background_job": ("domains.finance.services.payouts.payout_batch_service", "start_auto_payout_background_job"),
    "stop_auto_payout_background_job": ("domains.finance.services.payouts.payout_batch_service", "stop_auto_payout_background_job"),
    "run_auto_payout_sweep": ("domains.finance.services.payouts.payout_batch_service", "run_auto_payout_sweep"),
    "run_auto_logistics_payout_sweep": ("domains.finance.services.payouts.payout_batch_service", "run_auto_logistics_payout_sweep"),
    "list_periods": ("domains.finance.services.ledger.general_ledger", "list_periods"),
    "reverse_journal_entry": ("domains.finance.services.ledger.je_reversal_service", "reverse_journal_entry"),
    "generate_forecast": ("domains.finance.services.treasury.cash_management_service", "generate_forecast"),
    "Coupon": ("domains.promotions.models.promotions", "Coupon"),
    # Model re-exports (for cross-domain column access)
    "JournalEntry": ("domains.finance.models.finance", "JournalEntry"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Accounting controller facade (Law 3 sanctioned cross-domain surface). The
# controller module is exposed directly so callers may use it as a namespace
# (`accounting_controller.seed_chart_of_accounts(db)`).
import domains.finance.services.ledger.accounting_controller as accounting_controller  # noqa: E402,F401
