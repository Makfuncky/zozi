"""finance domain - dashboard / reporting read service.

Consolidates the read-heavy finance dashboard and report queries that used to
live inline in ``modules/employee/routers/finance.py`` (ED1). All finance-domain
models are queried directly here because they belong to this domain. The only
cross-domain read (``Payout``) goes through ``domains.payments.ports`` per
NEW_STRUCTURE.md Law 3.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domains.finance.models.finance import (
    Account,
    AccountBalance,
    GatewaySettlementSchedule,
    JournalEntry,
    JournalEntryLine,
    SupplierSettlement,
    TreasuryAccount,
)
from domains.payments.ports import list_payouts


class FinanceDashboardService:
    """Read-oriented service for finance dashboards and reports."""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self) -> dict:
        total_cash = self.db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.like("1010%"))
        ).scalar() or Decimal("0.00")

        total_liabilities = self.db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.in_(["2010", "2020", "2040"]))
        ).scalar() or Decimal("0.00")

        total_revenue = self.db.execute(
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

    def get_ledger(
        self,
        start_date: date,
        end_date: date,
        account_code: Optional[str] = None,
    ) -> list:
        query = select(JournalEntry).where(
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
        )

        if account_code:
            query = query.join(JournalEntryLine).join(Account).where(
                Account.code == account_code
            )

        entries = self.db.execute(
            query.order_by(JournalEntry.entry_date.desc())
        ).scalars().all()

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

    def get_vat_liability(self, period: str) -> dict:
        accounts = self.db.execute(
            select(AccountBalance)
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code.in_(["2040", "2050"]))
        ).scalars().all()

        output_vat = sum(
            b.balance
            for b in accounts
            if b.account_id
            and self.db.execute(
                select(Account.code).where(Account.id == b.account_id)
            ).scalar()
            == "2040"
        )
        input_vat = sum(
            b.balance
            for b in accounts
            if b.account_id
            and self.db.execute(
                select(Account.code).where(Account.id == b.account_id)
            ).scalar()
            == "2050"
        )

        return {
            "period": period,
            "output_vat_collected": float(output_vat),
            "input_vat_paid": float(input_vat),
            "net_vat_due": float(output_vat - input_vat),
        }

    def get_payout_batches(self) -> list:
        batches = list_payouts(self.db)
        batches = sorted(batches, key=lambda b: b.created_at, reverse=True)
        return [
            {
                "id": b.id,
                "batch_number": b.batch_number
                if hasattr(b, "batch_number")
                else f"PB-{b.id}",
                "total_amount": float(b.amount),
                "status": b.status,
                "created_at": b.created_at.isoformat(),
            }
            for b in batches
        ]

    def get_cash_position(self) -> dict:
        accounts = self.db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True)  # noqa: E712
        ).scalars().all()

        buckets = []
        total = Decimal("0")
        for a in accounts:
            buckets.append(
                {
                    "slug": a.slug,
                    "name": a.name,
                    "account_type": a.account_type,
                    "balance": float(a.balance),
                    "currency": a.currency,
                    "gl_account_code": a.gl_account_code,
                }
            )
            total += a.balance

        return {"total_cash": float(total), "buckets": buckets}

    def get_liabilities_exposure(self) -> dict:
        codes = {
            "2010": "supplier_payables",
            "2020": "logistics_payables",
            "2040": "vat_payable",
        }
        exposure = {}
        for code, label in codes.items():
            bal = self.db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code)
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure

    def supplier_earnings_report(self) -> list:
        rows = self.db.execute(
            select(
                SupplierSettlement.supplier_id,
                func.sum(SupplierSettlement.gross_amount).label("gross"),
                func.sum(SupplierSettlement.commission_amount).label("commission"),
                func.sum(SupplierSettlement.net_amount).label("net"),
            ).group_by(SupplierSettlement.supplier_id)
        ).all()
        return [
            {
                "supplier_id": r.supplier_id,
                "gross": float(r.gross),
                "commission": float(r.commission),
                "net": float(r.net),
            }
            for r in rows
        ]

    def gateway_exceptions(self) -> list:
        issues = self.db.execute(
            select(GatewaySettlementSchedule)
            .where(GatewaySettlementSchedule.status.in_(["pending", "flagged"]))
            .limit(50)
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
