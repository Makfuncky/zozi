#!python
"""
Finance Command Center API Endpoints
Implements GCC-tailored Chart of Accounts and Treasury Engine APIs
"""

import json
import os
from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from db.database import get_db
from models import (
    JournalEntry, JournalEntryLine, Account, User, AccountBalance, Payout,
    TreasuryAccount, GatewaySettlementSchedule, CashPositionSnapshot,
    PendingJournalEntry, PayoutBatch,
)
from services.treasury_engine import TreasuryEngine, seed_chart_of_accounts
from dependencies.auth import get_current_user
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter()


def get_treasury_engine(db: Session = Depends(get_db)) -> TreasuryEngine:
    return TreasuryEngine(db)


def require_finance_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role", "").lower() not in ("admin", "finance_admin", "country_head"):
        raise HTTPException(status_code=403, detail="Finance admin access required")
    return current_user


@router.post("/seed-coa")
def seed_coa(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_finance_admin),
):
    """Seed the Chart of Accounts (idempotent)."""
    seed_chart_of_accounts(db)
    return {"status": "Chart of Accounts seeded"}


@router.get("/dashboard/metrics")
def get_dashboard_metrics(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get real-time finance dashboard metrics (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        total_cash = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.like("1010%"))
        ).scalar() or Decimal("0.00")

        total_liabilities = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.in_(["2010", "2020", "2040"]))
        ).scalar() or Decimal("0.00")

        total_revenue = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.in_(["4010", "4020"]))
        ).scalar() or Decimal("0.00")

        return {
            "free_cash": float(total_cash),
            "total_liabilities": float(total_liabilities),
            "total_revenue": float(total_revenue),
            "net_income": float(total_revenue - total_liabilities),
        }
    finally:
        if country_code:
            clear_rls_context()


@router.get("/ledger")
def get_ledger(
    start_date: date = Query(...),
    end_date: date = Query(...),
    account_code: Optional[str] = None,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """Get journal entries with optional filters (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = select(JournalEntry).where(
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
        )

        if account_code:
            query = query.join(JournalEntryLine).join(Account).where(
                Account.code == account_code
            )

        entries = db.execute(query.order_by(JournalEntry.entry_date.desc())).scalars().all()

        return [
            {
                "id": e.id,
                "reference_number": e.reference_number,
                "entry_date": e.entry_date.isoformat(),
                "description": e.description,
                "source": e.source,
                "lines": [
                    {
                        "account_code": line.account.code if line.account else None,
                        "debit": float(line.amount) if line.side == "debit" else 0,
                        "credit": float(line.amount) if line.side == "credit" else 0,
                    }
                    for line in e.lines
                ],
            }
            for e in entries
        ]
    finally:
        if country_code:
            clear_rls_context()


@router.post("/ledger/entry")
def create_journal_entry(
    lines: List[dict],
    description: str,
    entry_date: date,
    source: str,
    treasury: TreasuryEngine = Depends(get_treasury_engine),
    current_user: dict = Depends(require_finance_admin),
):
    """Post a new journal entry."""
    entry = treasury.post_journal_entry(
        lines=lines,
        description=description,
        entry_date=entry_date,
        source=source,
    )
    return {"entry_id": entry.id, "reference_number": entry.reference_number}


@router.get("/trial-balance")
def get_trial_balance(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """Get trial balance report (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        treasury = TreasuryEngine(db)
        return treasury.get_trial_balance()
    finally:
        if country_code:
            clear_rls_context()


@router.get("/vat/liability")
def get_vat_liability(
    period: str = Query(...),
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """Calculate VAT liability for a period (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        accounts = db.execute(
            select(AccountBalance)
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.in_(["2040", "2050"]))
        ).scalars().all()

        output_vat = sum(b.balance for b in accounts if b.account_id and
                         db.execute(select(Account.code).where(Account.id == b.account_id)).scalar() == "2040")
        input_vat = sum(b.balance for b in accounts if b.account_id and
                        db.execute(select(Account.code).where(Account.id == b.account_id)).scalar() == "2050")

        return {
            "period": period,
            "output_vat_collected": float(output_vat),
            "input_vat_paid": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
        }
    finally:
        if country_code:
            clear_rls_context()


@router.post("/payouts/batch/generate")
def generate_payout_batch(
    country_code: str,
    cutoff_date: date,
    treasury: TreasuryEngine = Depends(get_treasury_engine),
):
    """Generate a new payout batch."""
    batch = treasury.generate_payout_batch(
        country_code=country_code,
        cutoff_date=cutoff_date,
    )
    return {"batch": batch}


@router.post("/payouts/batch/{batch_id}/approve")
def approve_payout_batch(
    batch_id: int,
    approver_id: int,
    treasury: TreasuryEngine = Depends(get_treasury_engine),
):
    """Approve a payout batch (maker-checker)."""
    success = treasury.approve_payout_batch(batch_id, approver_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"status": "approved"}


@router.get("/payouts/batches")
def get_payout_batches(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """List all payout batches (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        batches = db.execute(
            select(Payout).order_by(Payout.created_at.desc())
        ).scalars().all()

        return [
            {
                "id": b.id,
                "batch_number": b.batch_number if hasattr(b, 'batch_number') else f"PB-{b.id}",
                "total_amount": float(b.amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
            }
            for b in batches
        ]
    finally:
        if country_code:
            clear_rls_context()


# ── Finance Command Center (Spec Endpoints) ─────────────────────────


@router.get("/cash-position")
def get_cash_position(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """Breakdown of cash by treasury account (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)
        ).scalars().all()

        buckets = []
        total = Decimal("0")
        for a in accounts:
            buckets.append({
                "slug": a.slug,
                "name": a.name,
                "account_type": a.account_type,
                "balance": float(a.balance),
                "currency": a.currency,
                "gl_account_code": a.gl_account_code,
            })
            total += a.balance

        return {"total_cash": float(total), "buckets": buckets}
    finally:
        if country_code:
            clear_rls_context()


@router.get("/liabilities/exposure")
def get_liabilities_exposure(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
):
    """Total supplier/logistics/VAT payables (optionally country-scoped)."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2040": "vat_payable"}
        exposure = {}
        for code, label in codes.items():
            bal = db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code)
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure
    finally:
        if country_code:
            clear_rls_context()


@router.post("/ledger/manual-adjustment")
def manual_adjustment(
    debit_account: str = Body(...),
    credit_account: str = Body(...),
    amount: Decimal = Body(...),
    reason: str = Body(...),
    created_by: int = Body(...),
    current_user: dict = Depends(require_finance_admin),
    treasury: TreasuryEngine = Depends(get_treasury_engine),
):
    """Create a manual journal entry (Maker-Checker if amount > threshold)."""
    lines = [
        {"account_code": debit_account, "debit": float(amount), "description": reason},
        {"account_code": credit_account, "credit": float(amount), "description": reason},
    ]
    threshold = Decimal(os.getenv("MANUAL_ADJUST_THRESHOLD", "10000"))
    if amount > threshold:
        pending = treasury.submit_pending_entry(
            lines=lines, description=reason,
            created_by=created_by, source="manual_adjustment",
        )
        return {"status": "pending_approval", "pending_id": pending["pending_id"]}
    entry = treasury.post_journal_entry(
        lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
    )
    return {"entry_id": entry.id, "reference_number": entry.reference_number}


@router.get("/reports/supplier-earnings")
def supplier_earnings_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Exportable supplier earnings summary."""
    from models import SupplierSettlement
    rows = db.execute(
        select(
            SupplierSettlement.supplier_id,
            func.sum(SupplierSettlement.gross_amount).label("gross"),
            func.sum(SupplierSettlement.commission_amount).label("commission"),
            func.sum(SupplierSettlement.net_amount).label("net"),
        ).group_by(SupplierSettlement.supplier_id)
    ).all()
    return [
        {"supplier_id": r.supplier_id, "gross": float(r.gross), "commission": float(r.commission), "net": float(r.net)}
        for r in rows
    ]


@router.get("/reconciliation/gateway-exceptions")
def gateway_exceptions(db: Session = Depends(get_db)):
    """Orders where gateway says paid but settlement hasn't matched."""
    issues = db.execute(
        select(GatewaySettlementSchedule).where(
            GatewaySettlementSchedule.status.in_(["pending", "flagged"])
        ).limit(50)
    ).scalars().all()
    return [
        {
            "id": s.id,
            "gateway_id": s.gateway_id,
            "settlement_date": s.settlement_date.isoformat(),
            "amount": float(s.amount),
            "status": s.status,
        }
        for s in issues
    ]


@router.post("/reconciliation/cod-remittance")
def record_cod_remittance(
    logistics_partner_id: int = Body(...),
    amount_remitted: Decimal = Body(...),
    bank_reference: str = Body(...),
    proof_url: str = Body(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Clear COD Receivable (1030) → Cash Operating (1010)."""
    treasury = TreasuryEngine(db)
    entry = treasury.post_journal_entry(
        lines=[
            {"account_code": "1010", "debit": float(amount_remitted), "description": f"COD remittance {bank_reference}"},
            {"account_code": "1030", "credit": float(amount_remitted), "description": f"COD remittance {bank_reference}"},
        ],
        description=f"COD remittance from partner {logistics_partner_id}",
        source="cod_remittance",
        created_by=current_user.get("id"),
    )
    return {
        "entry_id": entry.id,
        "reference_number": entry.reference_number,
        "amount_remitted": float(amount_remitted),
    }


# ── Maker-Checker Endpoints ──────────────────────────────────────────


@router.get("/ledger/pending")
def list_pending_entries(treasury: TreasuryEngine = Depends(get_treasury_engine)):
    return {"entries": treasury.list_pending_entries()}


@router.post("/ledger/pending/{pending_id}/approve")
def approve_pending(
    pending_id: int,
    approver_id: int = Body(...),
    treasury: TreasuryEngine = Depends(get_treasury_engine),
):
    return treasury.approve_pending_entry(pending_id, approver_id)


@router.post("/ledger/pending/{pending_id}/reject")
def reject_pending(
    pending_id: int,
    rejected_by: int = Body(...),
    reason: str = Body(...),
    treasury: TreasuryEngine = Depends(get_treasury_engine),
):
    return treasury.reject_pending_entry(pending_id, rejected_by, reason)


# ── Orphan Detector ──────────────────────────────────────────────────


@router.post("/detect-orphans")
def detect_orphans(treasury: TreasuryEngine = Depends(get_treasury_engine)):
    alerts = treasury.run_orphan_detector()
    return {"alerts": alerts, "count": len(alerts)}
