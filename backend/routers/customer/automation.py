from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from utils.dependencies import require_admin
from services import automation_scheduler as scheduler
from services.gateway_reconciliation_service import (
    match_gateway_settlement,
    reconcile_cod_deposit,
    run_gateway_3way_reconciliation,
)
from services.ai_automation_service import (
    run_ai_bank_reconciliation,
    process_email_inbox,
    process_email_invoice,
    process_mobile_scan,
    batch_categorize_all,
    categorize_expense_ai,
)
from services.payout_batch_service import (
    generate_supplier_payout_batches,
    generate_logistics_payout_batches,
    get_pending_batches_for_supplier,
    supplier_approve_batch,
)
from services.refund_posting_service import post_refund_automatically
from services.credit_control_service import (
    check_customer_credit,
    enforce_auto_credit_holds,
    get_customer_credit_summary,
)

router = APIRouter()


@router.post("/run", summary="Run full automation suite")
def run_automation(country_code: str = None, period_year: int = None,
                    period_month: int = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return scheduler.run_full_automation(db, country_code=country_code,
                                          period_year=period_year,
                                          period_month=period_month)


@router.post("/cash-snapshot", summary="Take cash position snapshot")
def cash_snapshot(country_code: str = None, db: Session = Depends(get_db),
                   _admin: dict = Depends(require_admin)):
    return scheduler.take_cash_snapshot(db, country_code=country_code)


@router.post("/vat", summary="Compute VAT remittance for a period")
def compute_vat(period_year: int, period_month: int, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.compute_vat_remittance(db, period_year, period_month, country_code)


@router.post("/reports", summary="Generate period financial reports")
def generate_reports(period_year: int, period_month: int, country_code: str = None,
                      db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return scheduler.generate_period_reports(db, period_year, period_month, country_code)


@router.post("/statements/distributors", summary="Generate distributor statements")
def distributor_statements(period_year: int, period_month: int, country_code: str = None,
                            db: Session = Depends(get_db),
                            _admin: dict = Depends(require_admin)):
    return scheduler.generate_distributor_statements(db, period_year, period_month, country_code)


@router.post("/statements/suppliers", summary="Generate supplier statements")
def supplier_statements(period_year: int, period_month: int, country_code: str = None,
                         db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    return scheduler.generate_supplier_statements(db, period_year, period_month, country_code)


@router.post("/alerts", summary="Run alert engine")
def run_alerts(country_code: str = None, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    return scheduler.run_alert_engine(db, country_code=country_code)


# ── Gateway Reconciliation (#4, #5, #7) ───────────────────────────────────


@router.post("/gateway-reconciliation/run", summary="Run 3-way gateway reconciliation")
def run_gateway_reconciliation(country_code: str = None, db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Run 3-way gateway reconciliation (order vs gateway vs bank)."""
    return run_gateway_3way_reconciliation(db, country_code)


@router.post("/gateway-reconciliation/match/{settlement_id}", summary="Match a gateway settlement")
def match_settlement(settlement_id: int, bank_statement_line_id: int = None,
                      country_code: str = None, db: Session = Depends(get_db),
                      _admin: dict = Depends(require_admin)):
    """Manually match a specific gateway settlement."""
    return match_gateway_settlement(db, settlement_id, bank_statement_line_id, country_code)


@router.post("/cod-reconcile/{order_id}", summary="Reconcile COD deposit for an order")
def cod_reconcile(order_id: int, deposited_amount: float, logistics_partner_id: int = None,
                   bank_transaction_id: int = None, country_code: str = None,
                   db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Reconcile COD cash deposit from logistics partner."""
    from decimal import Decimal
    return reconcile_cod_deposit(
        db, order_id, Decimal(str(deposited_amount)),
        logistics_partner_id, bank_transaction_id, country_code
    )


# ── Payout Batches (#14, #15) ─────────────────────────────────────────────


@router.post("/payout-batches/generate", summary="Generate supplier payout batches")
def generate_payout_batches(country_code: str = None, holding_days: int = 7,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Nightly cron: Generate payout batches from eligible settlements."""
    return generate_supplier_payout_batches(db, country_code, holding_days)


@router.post("/payout-batches/logistics", summary="Generate logistics payout batches")
def generate_logistics_batches(country_code: str = None, holding_days: int = 7,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Generate payout batches for logistics partners."""
    return generate_logistics_payout_batches(db, country_code, holding_days)


@router.get("/payout-batches/pending/{supplier_id}", summary="Get pending batches for supplier")
def pending_supplier_batches(supplier_id: int, db: Session = Depends(get_db)):
    """Get payout batches pending supplier approval."""
    return get_pending_batches_for_supplier(db, supplier_id)


@router.post("/payout-batches/{batch_id}/approve", summary="Supplier approves payout batch")
def approve_batch(batch_id: int, supplier_id: int, approved: bool = True,
                   notes: str = None, db: Session = Depends(get_db)):
    """Supplier self-approval for payout batch."""
    return supplier_approve_batch(db, batch_id, supplier_id, approved, notes)


# ── Refund Posting (#26) ──────────────────────────────────────────────────


@router.post("/refunds/{refund_id}/post", summary="Auto-post refund journal entries")
def post_refund(refund_id: int, approved_by: int = None, country_code: str = None,
                db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """Auto-post journal entries when a refund is approved."""
    return post_refund_automatically(db, refund_id, approved_by, country_code)


# ── Credit Control (#24) ──────────────────────────────────────────────────


@router.get("/credit-check/{customer_id}", summary="Check customer credit status")
def credit_check(customer_id: int, order_amount: float = None,
                  db: Session = Depends(get_db)):
    """Pre-dispatch credit check for a customer."""
    from decimal import Decimal
    return check_customer_credit(
        db, customer_id,
        Decimal(str(order_amount)) if order_amount else None
    )


@router.post("/credit-control/enforce", summary="Enforce auto credit holds")
def enforce_credit_holds(country_code: str = None, db: Session = Depends(get_db),
                          _admin: dict = Depends(require_admin)):
    """Daily cron: Auto-place/release credit holds."""
    return enforce_auto_credit_holds(db, country_code)


@router.get("/credit-summary/{customer_id}", summary="Get customer credit summary")
def credit_summary(customer_id: int, db: Session = Depends(get_db)):
    """Get comprehensive credit summary for a customer."""
    return get_customer_credit_summary(db, customer_id)


# ── AI Bank Reconciliation (#6) ───────────────────────────────


@router.post("/ai/bank-reconciliation", summary="Run AI fuzzy bank reconciliation")
def ai_bank_recon(country_code: str = None, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    """AI-powered fuzzy bank reconciliation using semantic matching."""
    return run_ai_bank_reconciliation(db, country_code)


# ── Email-to-Ledger (#8) ──────────────────────────────────────


@router.post("/email/inbox", summary="Process email inbox for invoices")
def process_email_inbox_endpoint(country_code: str = None,
                                  db: Session = Depends(get_db),
                                  _admin: dict = Depends(require_admin)):
    """Batch process email inbox for invoice emails."""
    return process_email_inbox(db, country_code)


@router.post("/email/process", summary="Process an invoice email")
def process_email_endpoint(email_text: str = Body(..., embed=True), sender: str = None,
                             country_code: str = None,
                             db: Session = Depends(get_db),
                             _admin: dict = Depends(require_admin)):
    """Process a single invoice email through OCR-to-ledger pipeline."""
    return process_email_invoice(db, email_text, sender, country_code)


# ── Mobile Scan Upload (#9) ───────────────────────────────────


@router.post("/mobile/scan", summary="Process mobile receipt scan")
def mobile_scan_endpoint(country_code: str = None,
                           db: Session = Depends(get_db),
                           _admin: dict = Depends(require_admin)):
    """Mobile upload endpoint - process receipt image through OCR to GL.
    Note: For binary upload, send as multipart/form-data with 'image' field.
    This endpoint returns the processing pipeline definition."""
    return {
        "status": "ready",
        "endpoint": "/automation/mobile/scan/upload",
        "method": "POST multipart/form-data",
        "fields": ["image (binary)", "vendor_name (optional)", "country_code (optional)"],
    }


# ── AI Categorization (#27) ───────────────────────────────────


@router.post("/ai/categorize/{expense_id}", summary="AI categorize a scanned expense")
def categorize_expense(expense_id: int, db: Session = Depends(get_db),
                         _admin: dict = Depends(require_admin)):
    """Use AI to categorize a scanned expense and auto-post to GL."""
    from decimal import Decimal
    return categorize_expense_ai(db, expense_id)


@router.post("/ai/categorize/batch", summary="Batch categorize all uncategorized expenses")
def batch_categorize_endpoint(country_code: str = None,
                                db: Session = Depends(get_db),
                                _admin: dict = Depends(require_admin)):
    """Batch categorize all uncategorized scanned expenses."""
    return batch_categorize_all(db, country_code)