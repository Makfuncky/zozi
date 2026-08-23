"""Auto-migrated service logic from routers/cash_management.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Body, Depends, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session

import modules.treasury.routers.cash_management_controller as ctrl

from modules.admin.routers.auth import require_admin, require_permission
from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    BadgeBillingOut,
    BankTransactionCreate,
    BankTransactionImportItem,
    BankTransactionOut,
    BankTransactionResolutionIn,
    FinanceBankConnectionTestOut,
    FinanceBankSettingsOut,
    FinanceBankSettingsUpdate,
    FinancialSummaryOut,
    LedgerEntryOut,
    LogisticsCODRemittanceReceiptOut,
    LogisticsFinancialSummaryOut,
    LogisticsSettlementOut,
    ReconciliationSummaryOut,
    RefundLedgerOut,
    SupplierFinancialSummaryOut,
    SupplierSettlementOut,
    VATRemittanceCreate,
    VATRemittanceOut,
)

from infrastructure.utils.dependencies import get_current_user

class FlagRequest(BaseModel):
    reason: str

class CodRemittanceRequest(BaseModel):
    amount: float

class BadgeBillingPaymentRequest(BaseModel):
    payment_method: str
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None

class PayoutProcessRequest(BaseModel):
    settlement_ids: list[int] = []

class ReceiptReviewRequest(BaseModel):
    note: Optional[str] = None

def admin_financial_summary(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_financial_summary(db)

def admin_reconciliation_summary(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_reconciliation_summary(db)

def admin_list_ledger(skip: int, limit: int, order_id: Optional[int], supplier_id: Optional[int], settlement_status: Optional[str], payment_method: Optional[str], category_slug: Optional[str], badge_level: Optional[str], calculation_method: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_ledger_entries(
        db, skip=skip, limit=limit,
        order_id=order_id, supplier_id=supplier_id,
        settlement_status=settlement_status, payment_method=payment_method,
        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,
    )

def admin_list_badge_billings(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], badge_level: Optional[str], charge_type: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_badge_billing_records(
        db,
        skip=skip,
        limit=limit,
        supplier_id=supplier_id,
        status=status,
        badge_level=badge_level,
        charge_type=charge_type,
    )

def admin_record_badge_billing_payment(billing_id: int, body: BadgeBillingPaymentRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_badge_billing_payment(
        billing_id=billing_id,
        payment_method=body.payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=body.transaction_ref,
        notes=body.notes,
    )
    db.commit()
    return result

def admin_list_supplier_settlements(skip: int, limit: int, supplier_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)

def admin_list_logistics_settlements(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)

def admin_list_bank_transactions(skip: int, limit: int, source: Optional[str], category: Optional[str], reconciled: Optional[bool], flagged: Optional[bool], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_bank_transactions(
        db, skip=skip, limit=limit,
        source=source, category=category,
        reconciled=reconciled, flagged=flagged,
    )

def admin_list_refunds(skip: int, limit: int, status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)

def admin_list_vat_remittances(skip: int, limit: int, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)

def admin_get_bank_settings(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_finance_bank_settings(db)

def admin_list_transfer_providers(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_transfer_providers(db)

def admin_test_bank_settings_connection(db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_test_finance_bank_connection(db)

def admin_upsert_bank_settings(body: FinanceBankSettingsUpdate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_record_vat_remittance(body: VATRemittanceCreate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_create_bank_transaction(data: BankTransactionCreate, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)
    db.commit()
    return result

def admin_import_bank_transactions(items: list[BankTransactionImportItem], auto_reconcile: bool, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_import_bank_transactions(
        [item.model_dump() for item in items],
        current_admin,
        db,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result

def admin_reconcile_transaction(txn_id: int, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)
    db.commit()
    return result

def admin_flag_transaction(txn_id: int, body: FlagRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)
    db.commit()
    return result

def admin_resolve_transaction(txn_id: int, body: BankTransactionResolutionIn, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)
    db.commit()
    return result

def admin_auto_reconcile_transactions(limit: int, source: Optional[str], category: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_auto_reconcile_transactions(
        current_admin,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    db.commit()
    return result

def admin_trigger_supplier_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}

def admin_trigger_logistics_payouts(body: Optional[PayoutProcessRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}

def admin_dispatch_payouts(kind: str, provider: Optional[str], dry_run: bool, background: bool, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    if background:
        return ctrl.admin_queue_dispatch_transfer_batch(
            kind,
            current_admin,
            provider=provider,
            dry_run=dry_run,
        )

    result = ctrl.admin_dispatch_transfer_batch(
        kind,
        current_admin,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    db.commit()
    return result

def admin_record_cod_remittance(settlement_id: int, body: CodRemittanceRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)
    db.commit()
    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}

def admin_list_cod_remittance_receipts(skip: int, limit: int, partner_id: Optional[int], status: Optional[str], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)

def admin_verify_cod_remittance_receipt(receipt_id: int, body: Optional[ReceiptReviewRequest], db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)
    db.commit()
    return result

def admin_reject_cod_remittance_receipt(receipt_id: int, body: ReceiptReviewRequest, db: Session, current_admin: dict):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")
    db.commit()
    return result

def supplier_financial_summary(db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return {"error": "Supplier access required"}, 403
    return ctrl.supplier_get_financial_summary(current_user["id"], db)

def supplier_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)

def supplier_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)

def logistics_financial_summary(db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return {"error": "Logistics partner not found"}, 404
    return ctrl.logistics_get_financial_summary(partner.id, db)

def logistics_list_settlements(skip: int, limit: int, status: Optional[str], db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)

def logistics_list_ledger(skip: int, limit: int, db: Session, current_user: dict):
    from domains.logistics.models.logistics import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)


