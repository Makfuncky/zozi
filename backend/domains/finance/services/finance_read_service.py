"""Finance read service (GET endpoints with direct DB aggregation).

The inline ``db.execute`` / ``select`` aggregation that previously lived in
``routers/finance.py`` is moved here so the router stays a thin delegator.
Each function mirrors the original endpoint's behaviour, including the
optional country-scoped RLS context. The TreasuryEngine-backed endpoints
(``trial_balance``, journal entry writes, payout-batch writes, etc.) are
not duplicated here — they already delegate to the treasury engine service.

All functions are pure data-access: they take a ``Session`` and return
serializable dicts/lists. No commits, no HTTP concerns.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    Account,
    AccountBalance,
    GatewaySettlementSchedule,
    JournalEntry,
    JournalEntryLine,
    Payout,
    SupplierSettlement,
    TreasuryAccount,
)
from infrastructure.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context


def _with_rls(db: Session, country_code: Optional[str]) -> Optional[str]:
    """Apply RLS context for a country-scoped query. Returns the code or None."""
    if country_code:
        code = country_code.upper()
        get_country_or_404(code, db)
        set_rls_context({code}, is_restricted=True)
        return code
    return None


def get_dashboard_metrics(db: Session, country_code: Optional[str] = None) -> dict:
    """Get real-time finance dashboard metrics (optionally country-scoped)."""
    code = _with_rls(db, country_code)
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
        if code:
            clear_rls_context()


def get_ledger(
    db: Session,
    start_date,
    end_date,
    account_code: Optional[str] = None,
    country_code: Optional[str] = None,
) -> list:
    """Get journal entries with optional filters (optionally country-scoped)."""
    code = _with_rls(db, country_code)
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
        if code:
            clear_rls_context()


def get_payout_batches(db: Session, country_code: Optional[str] = None) -> list:
    """List all payout batches (optionally country-scoped)."""
    code = _with_rls(db, country_code)
    try:
        batches = db.execute(
            select(Payout).order_by(Payout.created_at.desc())
        ).scalars().all()
        return [
            {
                "id": b.id,
                "batch_number": b.batch_number if hasattr(b, "batch_number") else f"PB-{b.id}",
                "total_amount": float(b.amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
            }
            for b in batches
        ]
    finally:
        if code:
            clear_rls_context()


def get_cash_position(db: Session, country_code: Optional[str] = None) -> dict:
    """Breakdown of cash by treasury account (optionally country-scoped)."""
    code = _with_rls(db, country_code)
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
        if code:
            clear_rls_context()


def get_liabilities_exposure(db: Session, country_code: Optional[str] = None) -> dict:
    """Total supplier/logistics/VAT payables (optionally country-scoped)."""
    code = _with_rls(db, country_code)
    try:
        codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2040": "vat_payable"}
        exposure = {}
        for code_key, label in codes.items():
            bal = db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code_key)
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure
    finally:
        if code:
            clear_rls_context()


def get_vat_liability(db: Session, period: str, country_code: Optional[str] = None) -> dict:
    """Calculate VAT liability for a period (optionally country-scoped)."""
    code = _with_rls(db, country_code)
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
        if code:
            clear_rls_context()


def get_supplier_earnings_report(db: Session) -> list:
    """Exportable supplier earnings summary."""
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


def get_gateway_exceptions(db: Session) -> list:
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

