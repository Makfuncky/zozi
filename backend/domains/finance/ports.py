"""finance domain - sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.finance.models`` or ``domains.finance.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

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


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)
from domains.finance.models.general_ledger import AutomationLog  # noqa: E402
from domains.finance.models.general_ledger import AutomationRule  # noqa: E402

from domains.finance.models.commission import CommissionAgreement, CommissionCategoryRate, CommissionLedgerEntry, ProductCommissionOverride
from domains.finance.models.erp import CustomsEntry, GoodsReceiptLine, GoodsReceiptNote, ImportCostTemplate, ImportShipment, ImportShipmentLine, LandedCostAllocation, PurchaseOrder, PurchaseOrderLine, SalesOrder, SalesOrderLine, StockMovement, Warehouse
from domains.finance.models.finance import APBill, APLedger, ARInvoice, ARLedgerEntry, Account, AccountBalance, AccountGroup, Accrual, BankAccount, BankMappingRule, BankReconciliation, BankStatementImport, BankStatementLine, BankTransaction, Budget, CashAccount, CashFlowForecast, CashPositionSnapshot, CashTransaction, CostCenter, Customer, FinanceAuditLog, FinanceAutomationLog, FiscalPeriod, FixedAsset, GatewaySettlementSchedule, Invoice, InvoiceItem, JournalEntry, JournalEntryLine, PayoutBatch, PayoutBatchItem, PendingJournalEntry, RecurringTemplate, RefundLedger, ScannedExpense, SupplierSettlement, TransactionLedger, TreasuryAccount, TreasuryTransaction, VATRemittance, Vendor


def get_commission_agreement_by_id(db: Session, id_: int) -> Optional[CommissionAgreement]:
    """Return CommissionAgreement by primary key (or None)."""
    return db.get(CommissionAgreement, id_)

def list_commission_agreements(db: Session, limit: int = 100) -> List[CommissionAgreement]:
    """Return up to ``limit`` CommissionAgreement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommissionAgreement, db, limit)

def list_commission_agreements_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommissionAgreement rows (scale-ready)."""
    return _keyset_page(CommissionAgreement, db, cursor, page_size)

def get_product_commission_override_by_id(db: Session, id_: int) -> Optional[ProductCommissionOverride]:
    """Return ProductCommissionOverride by primary key (or None)."""
    return db.get(ProductCommissionOverride, id_)

def list_product_commission_overrides(db: Session, limit: int = 100) -> List[ProductCommissionOverride]:
    """Return up to ``limit`` ProductCommissionOverride rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductCommissionOverride, db, limit)

def list_product_commission_overrides_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProductCommissionOverride rows (scale-ready)."""
    return _keyset_page(ProductCommissionOverride, db, cursor, page_size)

def get_commission_ledger_entry_by_id(db: Session, id_: int) -> Optional[CommissionLedgerEntry]:
    """Return CommissionLedgerEntry by primary key (or None)."""
    return db.get(CommissionLedgerEntry, id_)

def list_commission_ledger_entrys(db: Session, limit: int = 100) -> List[CommissionLedgerEntry]:
    """Return up to ``limit`` CommissionLedgerEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommissionLedgerEntry, db, limit)

def list_commission_ledger_entrys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommissionLedgerEntry rows (scale-ready)."""
    return _keyset_page(CommissionLedgerEntry, db, cursor, page_size)

def get_commission_category_rate_by_id(db: Session, id_: int) -> Optional[CommissionCategoryRate]:
    """Return CommissionCategoryRate by primary key (or None)."""
    return db.get(CommissionCategoryRate, id_)

def list_commission_category_rates(db: Session, limit: int = 100) -> List[CommissionCategoryRate]:
    """Return up to ``limit`` CommissionCategoryRate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommissionCategoryRate, db, limit)

def list_commission_category_rates_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommissionCategoryRate rows (scale-ready)."""
    return _keyset_page(CommissionCategoryRate, db, cursor, page_size)

def get_warehouse_by_id(db: Session, id_: int) -> Optional[Warehouse]:
    """Return Warehouse by primary key (or None)."""
    return db.get(Warehouse, id_)

def list_warehouses(db: Session, limit: int = 100) -> List[Warehouse]:
    """Return up to ``limit`` Warehouse rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Warehouse, db, limit)

def list_warehouses_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Warehouse rows (scale-ready)."""
    return _keyset_page(Warehouse, db, cursor, page_size)

def get_purchase_order_by_id(db: Session, id_: int) -> Optional[PurchaseOrder]:
    """Return PurchaseOrder by primary key (or None)."""
    return db.get(PurchaseOrder, id_)

def list_purchase_orders(db: Session, limit: int = 100) -> List[PurchaseOrder]:
    """Return up to ``limit`` PurchaseOrder rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PurchaseOrder, db, limit)

def list_purchase_orders_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PurchaseOrder rows (scale-ready)."""
    return _keyset_page(PurchaseOrder, db, cursor, page_size)

def get_purchase_order_line_by_id(db: Session, id_: int) -> Optional[PurchaseOrderLine]:
    """Return PurchaseOrderLine by primary key (or None)."""
    return db.get(PurchaseOrderLine, id_)

def list_purchase_order_lines(db: Session, limit: int = 100) -> List[PurchaseOrderLine]:
    """Return up to ``limit`` PurchaseOrderLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PurchaseOrderLine, db, limit)

def list_purchase_order_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PurchaseOrderLine rows (scale-ready)."""
    return _keyset_page(PurchaseOrderLine, db, cursor, page_size)

def get_goods_receipt_note_by_id(db: Session, id_: int) -> Optional[GoodsReceiptNote]:
    """Return GoodsReceiptNote by primary key (or None)."""
    return db.get(GoodsReceiptNote, id_)

def list_goods_receipt_notes(db: Session, limit: int = 100) -> List[GoodsReceiptNote]:
    """Return up to ``limit`` GoodsReceiptNote rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GoodsReceiptNote, db, limit)

def list_goods_receipt_notes_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of GoodsReceiptNote rows (scale-ready)."""
    return _keyset_page(GoodsReceiptNote, db, cursor, page_size)

def get_goods_receipt_line_by_id(db: Session, id_: int) -> Optional[GoodsReceiptLine]:
    """Return GoodsReceiptLine by primary key (or None)."""
    return db.get(GoodsReceiptLine, id_)

def list_goods_receipt_lines(db: Session, limit: int = 100) -> List[GoodsReceiptLine]:
    """Return up to ``limit`` GoodsReceiptLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GoodsReceiptLine, db, limit)

def list_goods_receipt_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of GoodsReceiptLine rows (scale-ready)."""
    return _keyset_page(GoodsReceiptLine, db, cursor, page_size)

def get_sales_order_by_id(db: Session, id_: int) -> Optional[SalesOrder]:
    """Return SalesOrder by primary key (or None)."""
    return db.get(SalesOrder, id_)

def list_sales_orders(db: Session, limit: int = 100) -> List[SalesOrder]:
    """Return up to ``limit`` SalesOrder rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SalesOrder, db, limit)

def list_sales_orders_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SalesOrder rows (scale-ready)."""
    return _keyset_page(SalesOrder, db, cursor, page_size)

def get_sales_order_line_by_id(db: Session, id_: int) -> Optional[SalesOrderLine]:
    """Return SalesOrderLine by primary key (or None)."""
    return db.get(SalesOrderLine, id_)

def list_sales_order_lines(db: Session, limit: int = 100) -> List[SalesOrderLine]:
    """Return up to ``limit`` SalesOrderLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SalesOrderLine, db, limit)

def list_sales_order_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SalesOrderLine rows (scale-ready)."""
    return _keyset_page(SalesOrderLine, db, cursor, page_size)

def get_stock_movement_by_id(db: Session, id_: int) -> Optional[StockMovement]:
    """Return StockMovement by primary key (or None)."""
    return db.get(StockMovement, id_)

def list_stock_movements(db: Session, limit: int = 100) -> List[StockMovement]:
    """Return up to ``limit`` StockMovement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(StockMovement, db, limit)

def list_stock_movements_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of StockMovement rows (scale-ready)."""
    return _keyset_page(StockMovement, db, cursor, page_size)

def get_import_shipment_by_id(db: Session, id_: int) -> Optional[ImportShipment]:
    """Return ImportShipment by primary key (or None)."""
    return db.get(ImportShipment, id_)

def list_import_shipments(db: Session, limit: int = 100) -> List[ImportShipment]:
    """Return up to ``limit`` ImportShipment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportShipment, db, limit)

def list_import_shipments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ImportShipment rows (scale-ready)."""
    return _keyset_page(ImportShipment, db, cursor, page_size)

def get_import_shipment_line_by_id(db: Session, id_: int) -> Optional[ImportShipmentLine]:
    """Return ImportShipmentLine by primary key (or None)."""
    return db.get(ImportShipmentLine, id_)

def list_import_shipment_lines(db: Session, limit: int = 100) -> List[ImportShipmentLine]:
    """Return up to ``limit`` ImportShipmentLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportShipmentLine, db, limit)

def list_import_shipment_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ImportShipmentLine rows (scale-ready)."""
    return _keyset_page(ImportShipmentLine, db, cursor, page_size)

def get_landed_cost_allocation_by_id(db: Session, id_: int) -> Optional[LandedCostAllocation]:
    """Return LandedCostAllocation by primary key (or None)."""
    return db.get(LandedCostAllocation, id_)

def list_landed_cost_allocations(db: Session, limit: int = 100) -> List[LandedCostAllocation]:
    """Return up to ``limit`` LandedCostAllocation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LandedCostAllocation, db, limit)

def list_landed_cost_allocations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LandedCostAllocation rows (scale-ready)."""
    return _keyset_page(LandedCostAllocation, db, cursor, page_size)

def get_customs_entry_by_id(db: Session, id_: int) -> Optional[CustomsEntry]:
    """Return CustomsEntry by primary key (or None)."""
    return db.get(CustomsEntry, id_)

def list_customs_entrys(db: Session, limit: int = 100) -> List[CustomsEntry]:
    """Return up to ``limit`` CustomsEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CustomsEntry, db, limit)

def list_customs_entrys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CustomsEntry rows (scale-ready)."""
    return _keyset_page(CustomsEntry, db, cursor, page_size)

def get_import_cost_template_by_id(db: Session, id_: int) -> Optional[ImportCostTemplate]:
    """Return ImportCostTemplate by primary key (or None)."""
    return db.get(ImportCostTemplate, id_)

def list_import_cost_templates(db: Session, limit: int = 100) -> List[ImportCostTemplate]:
    """Return up to ``limit`` ImportCostTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ImportCostTemplate, db, limit)

def list_import_cost_templates_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ImportCostTemplate rows (scale-ready)."""
    return _keyset_page(ImportCostTemplate, db, cursor, page_size)

def get_fiscal_period_by_id(db: Session, id_: int) -> Optional[FiscalPeriod]:
    """Return FiscalPeriod by primary key (or None)."""
    return db.get(FiscalPeriod, id_)

def list_fiscal_periods(db: Session, limit: int = 100) -> List[FiscalPeriod]:
    """Return up to ``limit`` FiscalPeriod rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FiscalPeriod, db, limit)

def list_fiscal_periods_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FiscalPeriod rows (scale-ready)."""
    return _keyset_page(FiscalPeriod, db, cursor, page_size)

def get_transaction_ledger_by_id(db: Session, id_: int) -> Optional[TransactionLedger]:
    """Return TransactionLedger by primary key (or None)."""
    return db.get(TransactionLedger, id_)

def list_transaction_ledgers(db: Session, limit: int = 100) -> List[TransactionLedger]:
    """Return up to ``limit`` TransactionLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TransactionLedger, db, limit)

def list_transaction_ledgers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TransactionLedger rows (scale-ready)."""
    return _keyset_page(TransactionLedger, db, cursor, page_size)

def get_supplier_settlement_by_id(db: Session, id_: int) -> Optional[SupplierSettlement]:
    """Return SupplierSettlement by primary key (or None)."""
    return db.get(SupplierSettlement, id_)

def list_supplier_settlements(db: Session, limit: int = 100) -> List[SupplierSettlement]:
    """Return up to ``limit`` SupplierSettlement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierSettlement, db, limit)

def list_supplier_settlements_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierSettlement rows (scale-ready)."""
    return _keyset_page(SupplierSettlement, db, cursor, page_size)

def get_journal_entry_by_id(db: Session, id_: int) -> Optional[JournalEntry]:
    """Return JournalEntry by primary key (or None)."""
    return db.get(JournalEntry, id_)

def list_journal_entrys(db: Session, limit: int = 100) -> List[JournalEntry]:
    """Return up to ``limit`` JournalEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(JournalEntry, db, limit)

def list_journal_entrys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of JournalEntry rows (scale-ready)."""
    return _keyset_page(JournalEntry, db, cursor, page_size)

def get_journal_entry_line_by_id(db: Session, id_: int) -> Optional[JournalEntryLine]:
    """Return JournalEntryLine by primary key (or None)."""
    return db.get(JournalEntryLine, id_)

def list_journal_entry_lines(db: Session, limit: int = 100) -> List[JournalEntryLine]:
    """Return up to ``limit`` JournalEntryLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(JournalEntryLine, db, limit)

def list_journal_entry_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of JournalEntryLine rows (scale-ready)."""
    return _keyset_page(JournalEntryLine, db, cursor, page_size)

def get_account_by_id(db: Session, id_: int) -> Optional[Account]:
    """Return Account by primary key (or None)."""
    return db.get(Account, id_)

def list_accounts(db: Session, limit: int = 100) -> List[Account]:
    """Return up to ``limit`` Account rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Account, db, limit)

def list_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Account rows (scale-ready)."""
    return _keyset_page(Account, db, cursor, page_size)

def get_account_group_by_id(db: Session, id_: int) -> Optional[AccountGroup]:
    """Return AccountGroup by primary key (or None)."""
    return db.get(AccountGroup, id_)

def list_account_groups(db: Session, limit: int = 100) -> List[AccountGroup]:
    """Return up to ``limit`` AccountGroup rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AccountGroup, db, limit)

def list_account_groups_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AccountGroup rows (scale-ready)."""
    return _keyset_page(AccountGroup, db, cursor, page_size)

def get_account_balance_by_id(db: Session, id_: int) -> Optional[AccountBalance]:
    """Return AccountBalance by primary key (or None)."""
    return db.get(AccountBalance, id_)

def list_account_balances(db: Session, limit: int = 100) -> List[AccountBalance]:
    """Return up to ``limit`` AccountBalance rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AccountBalance, db, limit)

def list_account_balances_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AccountBalance rows (scale-ready)."""
    return _keyset_page(AccountBalance, db, cursor, page_size)

def get_a_r_ledger_entry_by_id(db: Session, id_: int) -> Optional[ARLedgerEntry]:
    """Return ARLedgerEntry by primary key (or None)."""
    return db.get(ARLedgerEntry, id_)

def list_a_r_ledger_entrys(db: Session, limit: int = 100) -> List[ARLedgerEntry]:
    """Return up to ``limit`` ARLedgerEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ARLedgerEntry, db, limit)

def list_a_r_ledger_entrys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ARLedgerEntry rows (scale-ready)."""
    return _keyset_page(ARLedgerEntry, db, cursor, page_size)

def get_a_p_ledger_by_id(db: Session, id_: int) -> Optional[APLedger]:
    """Return APLedger by primary key (or None)."""
    return db.get(APLedger, id_)

def list_a_p_ledgers(db: Session, limit: int = 100) -> List[APLedger]:
    """Return up to ``limit`` APLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(APLedger, db, limit)

def list_a_p_ledgers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of APLedger rows (scale-ready)."""
    return _keyset_page(APLedger, db, cursor, page_size)


def get_invoice_by_id(db: Session, id_: int) -> Optional[Invoice]:
    """Return Invoice by primary key (or None)."""
    return db.get(Invoice, id_)

def list_invoices(db: Session, limit: int = 100) -> List[Invoice]:
    """Return up to ``limit`` Invoice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Invoice, db, limit)

def list_invoices_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Invoice rows (scale-ready)."""
    return _keyset_page(Invoice, db, cursor, page_size)

def get_invoice_item_by_id(db: Session, id_: int) -> Optional[InvoiceItem]:
    """Return InvoiceItem by primary key (or None)."""
    return db.get(InvoiceItem, id_)

def list_invoice_items(db: Session, limit: int = 100) -> List[InvoiceItem]:
    """Return up to ``limit`` InvoiceItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(InvoiceItem, db, limit)

def list_invoice_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of InvoiceItem rows (scale-ready)."""
    return _keyset_page(InvoiceItem, db, cursor, page_size)

def get_refund_ledger_by_id(db: Session, id_: int) -> Optional[RefundLedger]:
    """Return RefundLedger by primary key (or None)."""
    return db.get(RefundLedger, id_)

def list_refund_ledgers(db: Session, limit: int = 100) -> List[RefundLedger]:
    """Return up to ``limit`` RefundLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RefundLedger, db, limit)

def list_refund_ledgers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of RefundLedger rows (scale-ready)."""
    return _keyset_page(RefundLedger, db, cursor, page_size)

def get_bank_transaction_by_id(db: Session, id_: int) -> Optional[BankTransaction]:
    """Return BankTransaction by primary key (or None)."""
    return db.get(BankTransaction, id_)

def list_bank_transactions(db: Session, limit: int = 100) -> List[BankTransaction]:
    """Return up to ``limit`` BankTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankTransaction, db, limit)

def list_bank_transactions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankTransaction rows (scale-ready)."""
    return _keyset_page(BankTransaction, db, cursor, page_size)

def get_v_a_t_remittance_by_id(db: Session, id_: int) -> Optional[VATRemittance]:
    """Return VATRemittance by primary key (or None)."""
    return db.get(VATRemittance, id_)

def list_v_a_t_remittances(db: Session, limit: int = 100) -> List[VATRemittance]:
    """Return up to ``limit`` VATRemittance rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VATRemittance, db, limit)

def list_v_a_t_remittances_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of VATRemittance rows (scale-ready)."""
    return _keyset_page(VATRemittance, db, cursor, page_size)

def get_cash_account_by_id(db: Session, id_: int) -> Optional[CashAccount]:
    """Return CashAccount by primary key (or None)."""
    return db.get(CashAccount, id_)

def list_cash_accounts(db: Session, limit: int = 100) -> List[CashAccount]:
    """Return up to ``limit`` CashAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashAccount, db, limit)

def list_cash_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CashAccount rows (scale-ready)."""
    return _keyset_page(CashAccount, db, cursor, page_size)

def get_cash_transaction_by_id(db: Session, id_: int) -> Optional[CashTransaction]:
    """Return CashTransaction by primary key (or None)."""
    return db.get(CashTransaction, id_)

def list_cash_transactions(db: Session, limit: int = 100) -> List[CashTransaction]:
    """Return up to ``limit`` CashTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashTransaction, db, limit)

def list_cash_transactions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CashTransaction rows (scale-ready)."""
    return _keyset_page(CashTransaction, db, cursor, page_size)

def get_treasury_account_by_id(db: Session, id_: int) -> Optional[TreasuryAccount]:
    """Return TreasuryAccount by primary key (or None)."""
    return db.get(TreasuryAccount, id_)

def list_treasury_accounts(db: Session, limit: int = 100) -> List[TreasuryAccount]:
    """Return up to ``limit`` TreasuryAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TreasuryAccount, db, limit)

def list_treasury_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TreasuryAccount rows (scale-ready)."""
    return _keyset_page(TreasuryAccount, db, cursor, page_size)

def get_treasury_transaction_by_id(db: Session, id_: int) -> Optional[TreasuryTransaction]:
    """Return TreasuryTransaction by primary key (or None)."""
    return db.get(TreasuryTransaction, id_)

def list_treasury_transactions(db: Session, limit: int = 100) -> List[TreasuryTransaction]:
    """Return up to ``limit`` TreasuryTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TreasuryTransaction, db, limit)

def list_treasury_transactions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TreasuryTransaction rows (scale-ready)."""
    return _keyset_page(TreasuryTransaction, db, cursor, page_size)

def get_cash_flow_forecast_by_id(db: Session, id_: int) -> Optional[CashFlowForecast]:
    """Return CashFlowForecast by primary key (or None)."""
    return db.get(CashFlowForecast, id_)

def list_cash_flow_forecasts(db: Session, limit: int = 100) -> List[CashFlowForecast]:
    """Return up to ``limit`` CashFlowForecast rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashFlowForecast, db, limit)

def list_cash_flow_forecasts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CashFlowForecast rows (scale-ready)."""
    return _keyset_page(CashFlowForecast, db, cursor, page_size)

def get_cash_position_snapshot_by_id(db: Session, id_: int) -> Optional[CashPositionSnapshot]:
    """Return CashPositionSnapshot by primary key (or None)."""
    return db.get(CashPositionSnapshot, id_)

def list_cash_position_snapshots(db: Session, limit: int = 100) -> List[CashPositionSnapshot]:
    """Return up to ``limit`` CashPositionSnapshot rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CashPositionSnapshot, db, limit)

def list_cash_position_snapshots_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CashPositionSnapshot rows (scale-ready)."""
    return _keyset_page(CashPositionSnapshot, db, cursor, page_size)

def get_gateway_settlement_schedule_by_id(db: Session, id_: int) -> Optional[GatewaySettlementSchedule]:
    """Return GatewaySettlementSchedule by primary key (or None)."""
    return db.get(GatewaySettlementSchedule, id_)

def list_gateway_settlement_schedules(db: Session, limit: int = 100) -> List[GatewaySettlementSchedule]:
    """Return up to ``limit`` GatewaySettlementSchedule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GatewaySettlementSchedule, db, limit)

def list_gateway_settlement_schedules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of GatewaySettlementSchedule rows (scale-ready)."""
    return _keyset_page(GatewaySettlementSchedule, db, cursor, page_size)

def get_pending_journal_entry_by_id(db: Session, id_: int) -> Optional[PendingJournalEntry]:
    """Return PendingJournalEntry by primary key (or None)."""
    return db.get(PendingJournalEntry, id_)

def list_pending_journal_entrys(db: Session, limit: int = 100) -> List[PendingJournalEntry]:
    """Return up to ``limit`` PendingJournalEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PendingJournalEntry, db, limit)

def list_pending_journal_entrys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PendingJournalEntry rows (scale-ready)."""
    return _keyset_page(PendingJournalEntry, db, cursor, page_size)

def get_payout_batch_by_id(db: Session, id_: int) -> Optional[PayoutBatch]:
    """Return PayoutBatch by primary key (or None)."""
    return db.get(PayoutBatch, id_)

def list_payout_batchs(db: Session, limit: int = 100) -> List[PayoutBatch]:
    """Return up to ``limit`` PayoutBatch rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PayoutBatch, db, limit)

def list_payout_batchs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PayoutBatch rows (scale-ready)."""
    return _keyset_page(PayoutBatch, db, cursor, page_size)

def get_payout_batch_item_by_id(db: Session, id_: int) -> Optional[PayoutBatchItem]:
    """Return PayoutBatchItem by primary key (or None)."""
    return db.get(PayoutBatchItem, id_)

def list_payout_batch_items(db: Session, limit: int = 100) -> List[PayoutBatchItem]:
    """Return up to ``limit`` PayoutBatchItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PayoutBatchItem, db, limit)

def list_payout_batch_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PayoutBatchItem rows (scale-ready)."""
    return _keyset_page(PayoutBatchItem, db, cursor, page_size)

def get_bank_mapping_rule_by_id(db: Session, id_: int) -> Optional[BankMappingRule]:
    """Return BankMappingRule by primary key (or None)."""
    return db.get(BankMappingRule, id_)

def list_bank_mapping_rules(db: Session, limit: int = 100) -> List[BankMappingRule]:
    """Return up to ``limit`` BankMappingRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankMappingRule, db, limit)

def list_bank_mapping_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankMappingRule rows (scale-ready)."""
    return _keyset_page(BankMappingRule, db, cursor, page_size)

def get_bank_statement_import_by_id(db: Session, id_: int) -> Optional[BankStatementImport]:
    """Return BankStatementImport by primary key (or None)."""
    return db.get(BankStatementImport, id_)

def list_bank_statement_imports(db: Session, limit: int = 100) -> List[BankStatementImport]:
    """Return up to ``limit`` BankStatementImport rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankStatementImport, db, limit)

def list_bank_statement_imports_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankStatementImport rows (scale-ready)."""
    return _keyset_page(BankStatementImport, db, cursor, page_size)

def get_bank_statement_line_by_id(db: Session, id_: int) -> Optional[BankStatementLine]:
    """Return BankStatementLine by primary key (or None)."""
    return db.get(BankStatementLine, id_)

def list_bank_statement_lines(db: Session, limit: int = 100) -> List[BankStatementLine]:
    """Return up to ``limit`` BankStatementLine rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankStatementLine, db, limit)

def list_bank_statement_lines_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankStatementLine rows (scale-ready)."""
    return _keyset_page(BankStatementLine, db, cursor, page_size)

def get_fixed_asset_by_id(db: Session, id_: int) -> Optional[FixedAsset]:
    """Return FixedAsset by primary key (or None)."""
    return db.get(FixedAsset, id_)

def list_fixed_assets(db: Session, limit: int = 100) -> List[FixedAsset]:
    """Return up to ``limit`` FixedAsset rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FixedAsset, db, limit)

def list_fixed_assets_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FixedAsset rows (scale-ready)."""
    return _keyset_page(FixedAsset, db, cursor, page_size)

def get_accrual_by_id(db: Session, id_: int) -> Optional[Accrual]:
    """Return Accrual by primary key (or None)."""
    return db.get(Accrual, id_)

def list_accruals(db: Session, limit: int = 100) -> List[Accrual]:
    """Return up to ``limit`` Accrual rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Accrual, db, limit)

def list_accruals_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Accrual rows (scale-ready)."""
    return _keyset_page(Accrual, db, cursor, page_size)

def get_scanned_expense_by_id(db: Session, id_: int) -> Optional[ScannedExpense]:
    """Return ScannedExpense by primary key (or None)."""
    return db.get(ScannedExpense, id_)

def list_scanned_expenses(db: Session, limit: int = 100) -> List[ScannedExpense]:
    """Return up to ``limit`` ScannedExpense rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ScannedExpense, db, limit)

def list_scanned_expenses_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ScannedExpense rows (scale-ready)."""
    return _keyset_page(ScannedExpense, db, cursor, page_size)

def get_vendor_by_id(db: Session, id_: int) -> Optional[Vendor]:
    """Return Vendor by primary key (or None)."""
    return db.get(Vendor, id_)

def list_vendors(db: Session, limit: int = 100) -> List[Vendor]:
    """Return up to ``limit`` Vendor rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Vendor, db, limit)

def list_vendors_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Vendor rows (scale-ready)."""
    return _keyset_page(Vendor, db, cursor, page_size)

def get_customer_by_id(db: Session, id_: int) -> Optional[Customer]:
    """Return Customer by primary key (or None)."""
    return db.get(Customer, id_)

def list_customers(db: Session, limit: int = 100) -> List[Customer]:
    """Return up to ``limit`` Customer rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Customer, db, limit)

def list_customers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Customer rows (scale-ready)."""
    return _keyset_page(Customer, db, cursor, page_size)

def get_cost_center_by_id(db: Session, id_: int) -> Optional[CostCenter]:
    """Return CostCenter by primary key (or None)."""
    return db.get(CostCenter, id_)

def list_cost_centers(db: Session, limit: int = 100) -> List[CostCenter]:
    """Return up to ``limit`` CostCenter rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CostCenter, db, limit)

def list_cost_centers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CostCenter rows (scale-ready)."""
    return _keyset_page(CostCenter, db, cursor, page_size)

def get_a_p_bill_by_id(db: Session, id_: int) -> Optional[APBill]:
    """Return APBill by primary key (or None)."""
    return db.get(APBill, id_)

def list_a_p_bills(db: Session, limit: int = 100) -> List[APBill]:
    """Return up to ``limit`` APBill rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(APBill, db, limit)

def list_a_p_bills_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of APBill rows (scale-ready)."""
    return _keyset_page(APBill, db, cursor, page_size)

def get_a_r_invoice_by_id(db: Session, id_: int) -> Optional[ARInvoice]:
    """Return ARInvoice by primary key (or None)."""
    return db.get(ARInvoice, id_)

def list_a_r_invoices(db: Session, limit: int = 100) -> List[ARInvoice]:
    """Return up to ``limit`` ARInvoice rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ARInvoice, db, limit)

def list_a_r_invoices_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ARInvoice rows (scale-ready)."""
    return _keyset_page(ARInvoice, db, cursor, page_size)

def get_bank_account_by_id(db: Session, id_: int) -> Optional[BankAccount]:
    """Return BankAccount by primary key (or None)."""
    return db.get(BankAccount, id_)

def list_bank_accounts(db: Session, limit: int = 100) -> List[BankAccount]:
    """Return up to ``limit`` BankAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankAccount, db, limit)

def list_bank_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankAccount rows (scale-ready)."""
    return _keyset_page(BankAccount, db, cursor, page_size)

def get_budget_by_id(db: Session, id_: int) -> Optional[Budget]:
    """Return Budget by primary key (or None)."""
    return db.get(Budget, id_)

def list_budgets(db: Session, limit: int = 100) -> List[Budget]:
    """Return up to ``limit`` Budget rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Budget, db, limit)

def list_budgets_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Budget rows (scale-ready)."""
    return _keyset_page(Budget, db, cursor, page_size)

def get_bank_reconciliation_by_id(db: Session, id_: int) -> Optional[BankReconciliation]:
    """Return BankReconciliation by primary key (or None)."""
    return db.get(BankReconciliation, id_)

def list_bank_reconciliations(db: Session, limit: int = 100) -> List[BankReconciliation]:
    """Return up to ``limit`` BankReconciliation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BankReconciliation, db, limit)

def list_bank_reconciliations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BankReconciliation rows (scale-ready)."""
    return _keyset_page(BankReconciliation, db, cursor, page_size)

def get_recurring_template_by_id(db: Session, id_: int) -> Optional[RecurringTemplate]:
    """Return RecurringTemplate by primary key (or None)."""
    return db.get(RecurringTemplate, id_)

def list_recurring_templates(db: Session, limit: int = 100) -> List[RecurringTemplate]:
    """Return up to ``limit`` RecurringTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RecurringTemplate, db, limit)

def list_recurring_templates_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of RecurringTemplate rows (scale-ready)."""
    return _keyset_page(RecurringTemplate, db, cursor, page_size)

def get_finance_audit_log_by_id(db: Session, id_: int) -> Optional[FinanceAuditLog]:
    """Return FinanceAuditLog by primary key (or None)."""
    return db.get(FinanceAuditLog, id_)

def list_finance_audit_logs(db: Session, limit: int = 100) -> List[FinanceAuditLog]:
    """Return up to ``limit`` FinanceAuditLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FinanceAuditLog, db, limit)

def list_finance_audit_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FinanceAuditLog rows (scale-ready)."""
    return _keyset_page(FinanceAuditLog, db, cursor, page_size)

def get_finance_automation_log_by_id(db: Session, id_: int) -> Optional[FinanceAutomationLog]:
    """Return FinanceAutomationLog by primary key (or None)."""
    return db.get(FinanceAutomationLog, id_)

def list_finance_automation_logs(db: Session, limit: int = 100) -> List[FinanceAutomationLog]:
    """Return up to ``limit`` FinanceAutomationLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FinanceAutomationLog, db, limit)

def list_finance_automation_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FinanceAutomationLog rows (scale-ready)."""
    return _keyset_page(FinanceAutomationLog, db, cursor, page_size)

def get_automation_rule_by_id(db: Session, id_: int) -> Optional[AutomationRule]:
    """Return AutomationRule by primary key (or None)."""
    return db.get(AutomationRule, id_)

def list_automation_rules(db: Session, limit: int = 100) -> List[AutomationRule]:
    """Return up to ``limit`` AutomationRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AutomationRule, db, limit)

def list_automation_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AutomationRule rows (scale-ready)."""
    return _keyset_page(AutomationRule, db, cursor, page_size)

def get_automation_log_by_id(db: Session, id_: int) -> Optional[AutomationLog]:
    """Return AutomationLog by primary key (or None)."""
    return db.get(AutomationLog, id_)

def list_automation_logs(db: Session, limit: int = 100) -> List[AutomationLog]:
    """Return up to ``limit`` AutomationLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AutomationLog, db, limit)

def list_automation_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AutomationLog rows (scale-ready)."""
    return _keyset_page(AutomationLog, db, cursor, page_size)

# --- P11 re-exports (Law 3 sanctioned read/behavior surface) ---
from domains.finance.models.finance import Invoice, RefundLedger, TransactionLedger, TreasuryAccount
from domains.finance.services.ledger.finance_transfer_service import build_transfer_reference
from domains.finance.services.tax.tax_service import calculate_tax, get_country_config
# --- P11.5 re-exports (orders cross-domain repointing) ---
from domains.finance.services.treasury.cash_management_service import (
    apply_shipment_vehicle_selection,
    deserialize_pricing_breakdown_json,
    effective_allocation_delivery_amounts,
    list_cod_remittance_receipts,
    serialize_cod_remittance_receipt,
)
from domains.finance.services.ledger.sub_ledger_controller import controller_get_ar_summary, controller_get_ap_summary
from domains.finance.services.commission.commission_geography_service import list_badge_tiers, list_category_rates
from domains.finance.services.ledger.period_close_service import get_or_create_fiscal_period, get_current_fiscal_period, list_periods
from domains.finance.services.payments.payout_approval_read_service import list_pending_payouts
from domains.finance.services.payments.auto_payout_scheduler import get_background_job_status
from domains.finance.services.commission.commission_engine import get_effective_rate
from domains.finance.services.treasury.treasury_engine import TreasuryEngine
from domains.finance.services.payments.auto_payout_scheduler import start_auto_payout_background_job, stop_auto_payout_background_job, run_auto_payout_sweep, run_auto_logistics_payout_sweep
from domains.finance.services.treasury.cash_flow_forecast_service import generate_forecast
from domains.finance.services.treasury.cash_management_service import log_refund_bank_transaction
from domains.finance.services.treasury.cash_write_service import create_cash_account, create_cash_transaction
from domains.finance.services.commission.commission_geography_service import create_badge_tier, create_category_rate, update_badge_tier, update_category_rate
from domains.finance.services.ledger.expense_processing import ExpenseProcessingService
from domains.finance.services.finance import accounting_controller, trading_service
from domains.finance.services.ledger.finance_transfer_service import build_transfer_export_payload
from domains.finance.services.reporting.financial_reporting import FinancialReportingService
from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal, post_supplier_settlement_journal
from domains.finance.services.ledger.je_reversal_service import reverse_journal_entry
from domains.finance.services.payments.payout_approval_controller import approve_payout, reject_payout, approve_batch, reject_batch, dispatch_batch
from domains.finance.services.ledger.period_close_service import close_period
from domains.finance.services.ledger.sub_ledger_controller import controller_post_ar_invoice, controller_post_ar_payment, controller_post_ap_payable, controller_post_ap_payment
