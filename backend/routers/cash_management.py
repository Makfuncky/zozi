"""
Cash Management Router — financial dashboard, ledger, settlements, payouts, and reconciliation.

Provides endpoints for:
  - Admin: Full financial dashboard, ledger view, settlements, bank reconciliation, payouts
  - Supplier: Earnings summary, settlement history, transaction ledger
  - Logistics Partner: Delivery fee summary, COD tracking, settlement history
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.schemas import (
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
from routers.auth import get_current_user
from controllers.admin_controller import require_admin, require_permission
import controllers.cash_management_controller as ctrl

router = APIRouter()


# ── Pydantic request bodies ──────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/summary",
    response_model=FinancialSummaryOut,
    summary="Financial dashboard summary",
)
def admin_financial_summary(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_financial_summary(db)


@router.get(
    "/admin/reconciliation-summary",
    response_model=ReconciliationSummaryOut,
    summary="Bank reconciliation workload summary",
)
def admin_reconciliation_summary(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_reconciliation_summary(db)


@router.get("/admin/ledger", response_model=list[LedgerEntryOut])
def admin_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    order_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    settlement_status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    category_slug: Optional[str] = Query(None),
    badge_level: Optional[str] = Query(None),
    calculation_method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_ledger_entries(
        db, skip=skip, limit=limit,
        order_id=order_id, supplier_id=supplier_id,
        settlement_status=settlement_status, payment_method=payment_method,
        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,
    )


@router.get("/admin/badge-billings", response_model=list[BadgeBillingOut])
def admin_list_badge_billings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    badge_level: Optional[str] = Query(None),
    charge_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
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


@router.post("/admin/badge-billings/{billing_id}/record-payment", response_model=BadgeBillingOut)
def admin_record_badge_billing_payment(
    billing_id: int,
    body: BadgeBillingPaymentRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
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


@router.get("/admin/supplier-settlements", response_model=list[SupplierSettlementOut])
def admin_list_supplier_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)


@router.get("/admin/logistics-settlements", response_model=list[LogisticsSettlementOut])
def admin_list_logistics_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    partner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


@router.get("/admin/bank-transactions", response_model=list[BankTransactionOut])
def admin_list_bank_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    reconciled: Optional[bool] = Query(None),
    flagged: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_bank_transactions(
        db, skip=skip, limit=limit,
        source=source, category=category,
        reconciled=reconciled, flagged=flagged,
    )


@router.get("/admin/refunds", response_model=list[RefundLedgerOut])
def admin_list_refunds(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)


@router.get("/admin/vat-remittances", response_model=list[VATRemittanceOut])
def admin_list_vat_remittances(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)


@router.get("/admin/bank-settings", response_model=FinanceBankSettingsOut)
def admin_get_bank_settings(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_finance_bank_settings(db)


@router.get("/admin/transfer-providers")
def admin_list_transfer_providers(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_transfer_providers(db)


@router.post("/admin/bank-settings/test-connection", response_model=FinanceBankConnectionTestOut)
def admin_test_bank_settings_connection(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_test_finance_bank_connection(db)


@router.put("/admin/bank-settings", response_model=FinanceBankSettingsOut)
def admin_upsert_bank_settings(
    body: FinanceBankSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)
    db.commit()
    return result


@router.post("/admin/vat-remittances", response_model=VATRemittanceOut, status_code=201)
def admin_record_vat_remittance(
    body: VATRemittanceCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)
    db.commit()
    return result


@router.post("/admin/bank-transactions", response_model=BankTransactionOut, status_code=201)
def admin_create_bank_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)
    db.commit()
    return result


@router.post("/admin/bank-transactions/import")
def admin_import_bank_transactions(
    items: list[BankTransactionImportItem],
    auto_reconcile: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_import_bank_transactions(
        [item.model_dump() for item in items],
        current_admin,
        db,
        auto_reconcile=auto_reconcile,
    )
    db.commit()
    return result


@router.post("/admin/bank-transactions/{txn_id}/reconcile", response_model=BankTransactionOut)
def admin_reconcile_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)
    db.commit()
    return result


@router.post("/admin/bank-transactions/{txn_id}/flag", response_model=BankTransactionOut)
def admin_flag_transaction(
    txn_id: int,
    body: FlagRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)
    db.commit()
    return result


@router.post("/admin/bank-transactions/{txn_id}/resolve", response_model=BankTransactionOut)
def admin_resolve_transaction(
    txn_id: int,
    body: BankTransactionResolutionIn,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)
    db.commit()
    return result


@router.post("/admin/bank-transactions/auto-reconcile")
def admin_auto_reconcile_transactions(
    limit: int = Query(100, ge=1, le=500),
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
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


@router.post("/admin/payouts/supplier/process")
def admin_trigger_supplier_payouts(
    body: Optional[PayoutProcessRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}


@router.post("/admin/payouts/logistics/process")
def admin_trigger_logistics_payouts(
    body: Optional[PayoutProcessRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    db.commit()
    return {"processed": len(results), "payouts": results}


@router.post("/admin/payouts/{kind}/dispatch")
def admin_dispatch_payouts(
    kind: str,
    provider: Optional[str] = Query(None),
    dry_run: bool = Query(True),
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
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


@router.post("/admin/cod-remittance/{settlement_id}")
def admin_record_cod_remittance(
    settlement_id: int,
    body: CodRemittanceRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)
    db.commit()
    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}


@router.get("/admin/cod-remittance-receipts", response_model=list[LogisticsCODRemittanceReceiptOut])
def admin_list_cod_remittance_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    partner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


@router.post("/admin/cod-remittance-receipts/{receipt_id}/verify", response_model=LogisticsCODRemittanceReceiptOut)
def admin_verify_cod_remittance_receipt(
    receipt_id: int,
    body: Optional[ReceiptReviewRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)
    db.commit()
    return result


@router.post("/admin/cod-remittance-receipts/{receipt_id}/reject", response_model=LogisticsCODRemittanceReceiptOut)
def admin_reject_cod_remittance_receipt(
    receipt_id: int,
    body: ReceiptReviewRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")
    db.commit()
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/supplier/summary", response_model=SupplierFinancialSummaryOut)
def supplier_financial_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return {"error": "Supplier access required"}, 403
    return ctrl.supplier_get_financial_summary(current_user["id"], db)


@router.get("/supplier/settlements", response_model=list[SupplierSettlementOut])
def supplier_list_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)


@router.get("/supplier/ledger", response_model=list[LedgerEntryOut])
def supplier_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)


# ══════════════════════════════════════════════════════════════════════════════
# LOGISTICS PARTNER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/logistics/summary", response_model=LogisticsFinancialSummaryOut)
def logistics_financial_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from models import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return {"error": "Logistics partner not found"}, 404
    return ctrl.logistics_get_financial_summary(partner.id, db)


@router.get("/logistics/settlements", response_model=list[LogisticsSettlementOut])
def logistics_list_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from models import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)


@router.get("/logistics/ledger", response_model=list[LedgerEntryOut])
def logistics_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from models import LogisticsPartner
    partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == current_user["id"]).first()
    if not partner:
        return []
    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)

