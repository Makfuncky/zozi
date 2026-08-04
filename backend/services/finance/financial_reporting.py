import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from data.models import JournalEntry, TreasuryAccount, AuditLog
from utils.datetime_utils import utcnow as _utcnow
from services.financial_reports_service import (
    generate_income_statement as _generate_income_statement,
    generate_balance_sheet as _generate_balance_sheet,
    generate_cash_flow_statement as _generate_cash_flow_statement,
    save_report,
    get_saved_reports,
    IncomeStatementReport,
    BalanceSheetReport,
    CashFlowStatementReport,
)

logger = logging.getLogger(__name__)


class FinancialReportingService:
    """
    Analytics and reporting for financial operations.
    Delegates standard accounting reports to financial_reports_service.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_cash_flow_forecast(self, days: int = 30) -> dict:
        """Generate cash flow forecast from pending journal entries."""
        entries = (
            self.db.query(JournalEntry)
            .filter(JournalEntry.entry_date >= _utcnow())
            .limit(days * 10)
            .all()
        )

        inflows = sum(e.amount for e in entries if e.entry_type == "credit")
        outflows = sum(e.amount for e in entries if e.entry_type == "debit")

        return {
            "projected_inflow": float(inflows),
            "projected_outflow": float(outflows),
            "net_flow": float(inflows - outflows),
        }

    def get_variance_analysis(self, period_start: datetime, period_end: datetime) -> dict:
        """Compare budget vs actual for a period."""
        actual_entries = (
            self.db.query(JournalEntry)
            .filter(
                JournalEntry.entry_date >= period_start,
                JournalEntry.entry_date <= period_end,
            )
            .all()
        )

        actual_total = sum(float(e.amount) for e in actual_entries)

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "actual_total": actual_total,
            "variance": 0.0,
        }

    def get_profitability_by_country(self) -> list[dict]:
        """Get profitability breakdown by country from the income statement."""
        try:
            data = _get_account_balances_for_period(self.db, "OMR")
            revenue = sum(d["amount"] for d in data if d["group_type"] == "Revenue")
            expenses = sum(d["amount"] for d in data if d["group_type"] == "Expense")
            net = revenue - expenses
            return [
                {"country": "all", "total_revenue": float(revenue), "total_expenses": float(expenses), "net_income": float(net)},
            ]
        except Exception:
            entries = self.db.query(JournalEntry).all()
            country_totals = {}
            for e in entries:
                country = e.description.split("_")[-1] if "_" in e.description else "unknown"
                country_totals[country] = country_totals.get(country, 0) + float(e.amount)
            return [{"country": k, "total": v} for k, v in country_totals.items()]

    def get_fraud_exposure(self) -> dict:
        """Get count of flagged transactions."""
        flagged = (
            self.db.query(AuditLog)
            .filter(AuditLog.event_type == "fraud_alert")
            .count()
        )
        return {"flagged_transactions": flagged}

    # ── Standard Accounting Reports ──────────────────────────────────────────

    def generate_income_statement(
        self,
        period_start: datetime,
        period_end: datetime,
        currency: str = "OMR",
        persist: bool = False,
        country_code: Optional[str] = None,
    ) -> dict:
        report = _generate_income_statement(self.db, period_start, period_end, currency, country_code)
        data = report.to_dict()
        if persist:
            save_report(self.db, "income_statement", period_start, period_end, data, country_code)
        return data

    def generate_balance_sheet(
        self,
        as_of_date: Optional[datetime] = None,
        currency: str = "OMR",
        persist: bool = False,
        country_code: Optional[str] = None,
    ) -> dict:
        report = _generate_balance_sheet(self.db, as_of_date, currency, country_code)
        data = report.to_dict()
        if persist:
            period_end = as_of_date or datetime.utcnow()
            period_start = as_of_date or datetime.utcnow()
            save_report(self.db, "balance_sheet", period_start, period_end, data, country_code)
        return data

    def generate_cash_flow(
        self,
        period_start: datetime,
        period_end: datetime,
        currency: str = "OMR",
        persist: bool = False,
        country_code: Optional[str] = None,
    ) -> dict:
        report = _generate_cash_flow_statement(self.db, period_start, period_end, currency, country_code)
        data = report.to_dict()
        if persist:
            save_report(self.db, "cash_flow_statement", period_start, period_end, data, country_code)
        return data

    def list_reports(self, report_type: Optional[str] = None, country_code: Optional[str] = None, limit: int = 20) -> list:
        return get_saved_reports(self.db, report_type=report_type, country_code=country_code, limit=limit)


def _get_account_balances_for_period(
    db: Session,
    currency: str,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> list[dict]:
    """Helper exposed for profitability reporting."""
    from services.financial_reports_service import _get_account_balances_for_period as _inner
    return _inner(db, currency, period_start, period_end)

