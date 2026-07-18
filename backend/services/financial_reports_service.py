"""Financial Reports — Income Statement, Balance Sheet, Cash Flow Statement.

Generates standard accounting reports from the double-entry ledger (AccountBalance,
JournalEntry, JournalEntryLine) and persists them to the FinancialReport table.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from models import (
    Account,
    AccountBalance,
    AccountGroup,
    FinancialReport,
    JournalEntry,
    JournalEntryLine,
)
from utils.money import round_money

logger = logging.getLogger(__name__)


# ── Report output types ───────────────────────────────────────────────────


class IncomeStatementLine:
    def __init__(self, account_code: str, account_name: str, group_name: str, amount: Decimal):
        self.account_code = account_code
        self.account_name = account_name
        self.group_name = group_name
        self.amount = amount


class IncomeStatementReport:
    def __init__(
        self,
        period_start: datetime,
        period_end: datetime,
        revenue_lines: list[IncomeStatementLine],
        total_revenue: Decimal,
        expense_lines: list[IncomeStatementLine],
        total_expenses: Decimal,
        net_income: Decimal,
        currency: str,
    ):
        self.period_start = period_start
        self.period_end = period_end
        self.revenue_lines = revenue_lines
        self.total_revenue = total_revenue
        self.expense_lines = expense_lines
        self.total_expenses = total_expenses
        self.net_income = net_income
        self.currency = currency

    def to_dict(self) -> dict:
        return {
            "report_type": "income_statement",
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "currency": self.currency,
            "revenue": {
                "lines": [
                    {
                        "account_code": l.account_code,
                        "account_name": l.account_name,
                        "group_name": l.group_name,
                        "amount": float(l.amount),
                    }
                    for l in self.revenue_lines
                ],
                "total": float(self.total_revenue),
            },
            "expenses": {
                "lines": [
                    {
                        "account_code": l.account_code,
                        "account_name": l.account_name,
                        "group_name": l.group_name,
                        "amount": float(l.amount),
                    }
                    for l in self.expense_lines
                ],
                "total": float(self.total_expenses),
            },
            "net_income": float(self.net_income),
        }


class BalanceSheetLine:
    def __init__(self, account_code: str, account_name: str, group_name: str, amount: Decimal):
        self.account_code = account_code
        self.account_name = account_name
        self.group_name = group_name
        self.amount = amount


class BalanceSheetReport:
    def __init__(
        self,
        as_of_date: datetime,
        asset_lines: list[BalanceSheetLine],
        total_assets: Decimal,
        liability_lines: list[BalanceSheetLine],
        total_liabilities: Decimal,
        equity_lines: list[BalanceSheetLine],
        total_equity: Decimal,
        currency: str,
    ):
        self.as_of_date = as_of_date
        self.asset_lines = asset_lines
        self.total_assets = total_assets
        self.liability_lines = liability_lines
        self.total_liabilities = total_liabilities
        self.equity_lines = equity_lines
        self.total_equity = total_equity
        self.currency = currency

    def to_dict(self) -> dict:
        return {
            "report_type": "balance_sheet",
            "as_of_date": self.as_of_date.isoformat(),
            "currency": self.currency,
            "assets": {
                "lines": [
                    {
                        "account_code": l.account_code,
                        "account_name": l.account_name,
                        "group_name": l.group_name,
                        "amount": float(l.amount),
                    }
                    for l in self.asset_lines
                ],
                "total": float(self.total_assets),
            },
            "liabilities": {
                "lines": [
                    {
                        "account_code": l.account_code,
                        "account_name": l.account_name,
                        "group_name": l.group_name,
                        "amount": float(l.amount),
                    }
                    for l in self.liability_lines
                ],
                "total": float(self.total_liabilities),
            },
            "equity": {
                "lines": [
                    {
                        "account_code": l.account_code,
                        "account_name": l.account_name,
                        "group_name": l.group_name,
                        "amount": float(l.amount),
                    }
                    for l in self.equity_lines
                ],
                "total": float(self.total_equity),
            },
        }


class CashFlowLine:
    def __init__(self, label: str, amount: Decimal, account_codes: Optional[list[str]] = None):
        self.label = label
        self.amount = amount
        self.account_codes = account_codes or []


class CashFlowSection:
    def __init__(self, lines: list[CashFlowLine], total: Decimal):
        self.lines = lines
        self.total = total


class CashFlowStatementReport:
    def __init__(
        self,
        period_start: datetime,
        period_end: datetime,
        operating: CashFlowSection,
        net_operating: Decimal,
        investing: CashFlowSection,
        net_investing: Decimal,
        financing: CashFlowSection,
        net_financing: Decimal,
        net_change: Decimal,
        opening_balance: Decimal,
        closing_balance: Decimal,
        currency: str,
    ):
        self.period_start = period_start
        self.period_end = period_end
        self.operating = operating
        self.net_operating = net_operating
        self.investing = investing
        self.net_investing = net_investing
        self.financing = financing
        self.net_financing = net_financing
        self.net_change = net_change
        self.opening_balance = opening_balance
        self.closing_balance = closing_balance
        self.currency = currency

    def _section_dict(self, section: CashFlowSection, label: str) -> dict:
        return {
            "label": label,
            "lines": [
                {
                    "label": l.label,
                    "amount": float(l.amount),
                    "account_codes": l.account_codes,
                }
                for l in section.lines
            ],
            "total": float(section.total),
        }

    def to_dict(self) -> dict:
        return {
            "report_type": "cash_flow_statement",
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "currency": self.currency,
            "operating": self._section_dict(self.operating, "Operating Activities"),
            "net_operating": float(self.net_operating),
            "investing": self._section_dict(self.investing, "Investing Activities"),
            "net_investing": float(self.net_investing),
            "financing": self._section_dict(self.financing, "Financing Activities"),
            "net_financing": float(self.net_financing),
            "net_change": float(self.net_change),
            "opening_balance": float(self.opening_balance),
            "closing_balance": float(self.closing_balance),
        }


# ── Constants for account-type classification ────────────────────────────


def _get_account_type_from_code(code: str) -> str:
    prefix = code.split(".")[0][0] if "." in code else code[0]
    mapping = {
        "1": "Asset",
        "2": "Liability",
        "3": "Equity",
        "4": "Revenue",
        "5": "Expense",
    }
    return mapping.get(prefix, "Unknown")


# ── Helpers ────────────────────────────────────────────────────────────────


def _get_account_balances_for_period(
    db: Session,
    currency: str,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    country_code: Optional[str] = None,
) -> list[dict]:
    """Get aggregated account balances from JournalEntryLines for a period.

    Returns list of dicts with account_code, account_name, group_name,
    group_type, normal_side, and net_change.

    When period is provided, computes the net change (flow) for the period.
    When no period is provided, returns the current AccountBalance snapshot.
    """
    if period_start is None and period_end is None:
        q = db.query(
            Account.code,
            Account.name,
            AccountGroup.name.label("group_name"),
            AccountGroup.account_type,
            Account.normal_side,
            AccountBalance.balance,
        ).join(AccountGroup, Account.group_id == AccountGroup.id).outerjoin(
            AccountBalance,
            (AccountBalance.account_id == Account.id)
            & (AccountBalance.currency == currency),
        ).filter(Account.is_active == True)

        if country_code:
            q = q.filter(AccountBalance.country_code == country_code)

        rows = q.order_by(Account.code).all()
        return [
            {
                "account_code": r.code,
                "account_name": r.name,
                "group_name": r.group_name,
                "group_type": r.account_type or _get_account_type_from_code(r.code),
                "normal_side": r.normal_side,
                "amount": r.balance or Decimal("0.00"),
            }
            for r in rows
        ]

    q = text("""
        SELECT
            a.code AS account_code,
            a.name AS account_name,
            ag.name AS group_name,
            ag.account_type AS group_type,
            a.normal_side,
            COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE 0 END), 0) AS total_debits,
            COALESCE(SUM(CASE WHEN jel.side = 'credit' THEN jel.amount ELSE 0 END), 0) AS total_credits
        FROM journal_entry_lines jel
        JOIN journal_entries je ON jel.entry_id = je.id
        JOIN accounts a ON jel.account_id = a.id
        JOIN account_groups ag ON a.group_id = ag.id
        WHERE a.is_active = true
          AND (:ps IS NULL OR je.entry_date >= :ps)
          AND (:pe IS NULL OR je.entry_date <= :pe)
          AND (a.currency = :cur OR :cur IS NULL)
          AND (:cc IS NULL OR je.country_code = :cc)
        GROUP BY a.id, a.code, a.name, ag.name, ag.account_type, a.normal_side
        ORDER BY a.code
    """)
    params = {
        "ps": period_start,
        "pe": period_end,
        "cur": currency,
        "cc": country_code,
    }
    rows = db.execute(q, params).fetchall()

    result = []
    for r in rows:
        account_code = r[0]
        normal_side = r[4]
        total_debits = Decimal(str(r[5] or 0))
        total_credits = Decimal(str(r[6] or 0))
        if normal_side == "debit":
            net_change = total_debits - total_credits
        else:
            net_change = total_credits - total_debits
        result.append({
            "account_code": account_code,
            "account_name": r[1],
            "group_name": r[2],
            "group_type": r[3] or _get_account_type_from_code(account_code),
            "normal_side": normal_side,
            "amount": net_change,
        })
    return result


def _compute_total_for_type(
    data: list[dict],
    group_types: list[str],
    side: Optional[str] = None,
) -> tuple[list[dict], Decimal]:
    """Filter account rows by group_type(s) and optionally by normal_side.

    Returns (filtered_lines, total_amount).
    """
    filtered = [
        d for d in data
        if d["group_type"] in group_types
        and (side is None or d["normal_side"] == side)
    ]
    total = round_money(sum(d["amount"] for d in filtered))
    return filtered, total


# ── Report Generators ──────────────────────────────────────────────────────


def generate_income_statement(
    db: Session,
    period_start: datetime,
    period_end: datetime,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> IncomeStatementReport:
    """Generate an Income Statement (P&L) for the given period."""
    data = _get_account_balances_for_period(db, currency, period_start, period_end, country_code)

    revenue_lines_raw, total_revenue = _compute_total_for_type(data, ["Revenue"], side="credit")
    expense_lines_raw, total_expenses = _compute_total_for_type(data, ["Expense"], side="debit")
    net_income = round_money(total_revenue - total_expenses)

    revenue_lines = [
        IncomeStatementLine(
            account_code=d["account_code"],
            account_name=d["account_name"],
            group_name=d["group_name"],
            amount=d["amount"],
        )
        for d in revenue_lines_raw
    ]
    expense_lines = [
        IncomeStatementLine(
            account_code=d["account_code"],
            account_name=d["account_name"],
            group_name=d["group_name"],
            amount=d["amount"],
        )
        for d in expense_lines_raw
    ]
    return IncomeStatementReport(
        period_start=period_start,
        period_end=period_end,
        revenue_lines=revenue_lines,
        total_revenue=total_revenue,
        expense_lines=expense_lines,
        total_expenses=total_expenses,
        net_income=net_income,
        currency=currency,
    )


def generate_balance_sheet(
    db: Session,
    as_of_date: Optional[datetime] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> BalanceSheetReport:
    """Generate a Balance Sheet as of a given date (or current)."""
    data = _get_account_balances_for_period(db, currency, country_code=country_code)

    asset_lines_raw, total_assets = _compute_total_for_type(data, ["Asset"], side="debit")
    liability_lines_raw, total_liabilities = _compute_total_for_type(data, ["Liability"], side="credit")
    equity_lines_raw, total_equity = _compute_total_for_type(data, ["Equity"], side="credit")

    # If no equity accounts exist yet, add a placeholder for retained earnings
    if not equity_lines_raw:
        # Compute net income across all periods as proxy for retained earnings
        net_income = round_money(Decimal(
            db.execute(text("""
                SELECT COALESCE(SUM(CASE WHEN a.normal_side = 'credit' THEN ab.balance ELSE 0 END), 0)
                     - COALESCE(SUM(CASE WHEN a.normal_side = 'debit' THEN ab.balance ELSE 0 END), 0)
                FROM account_balances ab
                JOIN accounts a ON ab.account_id = a.id
                JOIN account_groups ag ON a.group_id = ag.id
                WHERE ag.account_type IN ('Revenue', 'Expense')
                  AND ab.currency = :cur
            """), {"cur": currency}).scalar() or 0
        ))
        equity_lines_raw = [
            {
                "account_code": "3010",
                "account_name": "Retained Earnings (Auto)",
                "group_name": "Equity",
                "group_type": "Equity",
                "normal_side": "credit",
                "amount": net_income,
            },
        ]
        total_equity = net_income

    asset_lines = [
        BalanceSheetLine(
            account_code=d["account_code"],
            account_name=d["account_name"],
            group_name=d["group_name"],
            amount=d["amount"],
        )
        for d in asset_lines_raw
    ]
    liability_lines = [
        BalanceSheetLine(
            account_code=d["account_code"],
            account_name=d["account_name"],
            group_name=d["group_name"],
            amount=d["amount"],
        )
        for d in liability_lines_raw
    ]
    equity_lines = [
        BalanceSheetLine(
            account_code=d["account_code"],
            account_name=d["account_name"],
            group_name=d["group_name"],
            amount=d["amount"],
        )
        for d in equity_lines_raw
    ]

    return BalanceSheetReport(
        as_of_date=as_of_date or datetime.utcnow(),
        asset_lines=asset_lines,
        total_assets=total_assets,
        liability_lines=liability_lines,
        total_liabilities=total_liabilities,
        equity_lines=equity_lines,
        total_equity=total_equity,
        currency=currency,
    )


def generate_cash_flow_statement(
    db: Session,
    period_start: datetime,
    period_end: datetime,
    currency: str = "OMR",
    country_code: Optional[str] = None,
) -> CashFlowStatementReport:
    pnl = generate_income_statement(db, period_start, period_end, currency, country_code)
    net_income = pnl.net_income

    cash_acct = db.query(Account).filter(Account.code == "1010").first()
    opening_balance = Decimal("0.00")
    closing_balance = Decimal("0.00")
    if cash_acct:
        bal_q = db.query(AccountBalance).filter(
            AccountBalance.account_id == cash_acct.id,
            AccountBalance.currency == currency,
        )
        if country_code:
            bal_q = bal_q.filter(AccountBalance.country_code == country_code)
        bal = bal_q.first()
        if bal:
            closing_balance = bal.balance
            cc_where = " AND je.country_code = :cc " if country_code else " "
            cc_p = {"cc": country_code} if country_code else {}
            opening_balance = round_money(
                Decimal(
                    db.execute(text(f"""
                        SELECT COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE -jel.amount END), 0)
                        FROM journal_entry_lines jel
                        JOIN journal_entries je ON jel.entry_id = je.id
                        WHERE jel.account_id = :aid
                          AND je.entry_date < :ps
                          {cc_where if country_code else ''}
                    """), {"aid": cash_acct.id, "ps": period_start, **cc_p}).scalar() or 0
                )
            )
            opening_balance = round_money(closing_balance - (
                db.execute(text(f"""
                    SELECT COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE -jel.amount END), 0)
                    FROM journal_entry_lines jel
                    JOIN journal_entries je ON jel.entry_id = je.id
                    WHERE jel.account_id = :aid
                      AND je.entry_date >= :ps
                      AND je.entry_date <= :pe
                      {cc_where if country_code else ''}
                """), {"aid": cash_acct.id, "ps": period_start, "pe": period_end, **cc_p}).scalar() or 0
            ))

    operating_codes = {
        "1030": ("(Increase)/Decrease in Accounts Receivable", "asset"),
        "1040": ("(Increase)/Decrease in Gateway Receivable", "asset"),
        "1050": ("(Increase)/Decrease in Supplier Prepayments", "asset"),
        "2010": ("Increase/(Decrease) in Supplier Payables", "liability"),
        "2020": ("Increase/(Decrease) in Logistics Payables", "liability"),
        "2030": ("Increase/(Decrease) in Refund Reserve", "liability"),
        "2040": ("Increase/(Decrease) in VAT Payable", "liability"),
        "2050": ("Increase/(Decrease) in Commission Payable", "liability"),
        "2060": ("Increase/(Decrease) in Deferred Revenue", "liability"),
        "2070": ("Increase/(Decrease) in Gateway Payable", "liability"),
    }

    operating_lines = [
        CashFlowLine(label="Net Income", amount=Decimal(str(net_income))),
    ]

    cc_where = " AND je.country_code = :cc " if country_code else " "
    cc_p = {"cc": country_code} if country_code else {}
    for code, (label, kind) in operating_codes.items():
        acct = db.query(Account).filter(Account.code == code).first()
        if not acct:
            continue
        change = Decimal(
            str(
                db.execute(text(f"""
                    SELECT COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE -jel.amount END), 0)
                    FROM journal_entry_lines jel
                    JOIN journal_entries je ON jel.entry_id = je.id
                    WHERE jel.account_id = :aid
                      AND je.entry_date >= :ps
                      AND je.entry_date <= :pe
                      {cc_where if country_code else ''}
                """), {"aid": acct.id, "ps": period_start, "pe": period_end, **cc_p}).scalar() or 0
            )
        )
        if change != 0:
            if kind == "asset":
                adjusted = -change
            else:
                adjusted = change
            operating_lines.append(CashFlowLine(label=label, amount=adjusted, account_codes=[code]))

    total_operating = round_money(sum(l.amount for l in operating_lines))
    investing_lines: list[CashFlowLine] = []
    financing_lines: list[CashFlowLine] = []
    net_change = round_money(closing_balance - opening_balance)

    return CashFlowStatementReport(
        period_start=period_start,
        period_end=period_end,
        operating=CashFlowSection(lines=operating_lines, total=total_operating),
        net_operating=total_operating,
        investing=CashFlowSection(lines=investing_lines, total=Decimal("0.00")),
        net_investing=Decimal("0.00"),
        financing=CashFlowSection(lines=financing_lines, total=Decimal("0.00")),
        net_financing=Decimal("0.00"),
        net_change=net_change,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        currency=currency,
    )


def save_report(
    db: Session,
    report_type: str,
    period_start: datetime,
    period_end: datetime,
    data: dict[str, Any],
    country_code: Optional[str] = None,
) -> FinancialReport:
    report = FinancialReport(
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        country_code=country_code,
        data=data,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_saved_reports(
    db: Session,
    report_type: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 20,
) -> list[FinancialReport]:
    q = db.query(FinancialReport).order_by(FinancialReport.generated_at.desc())
    if report_type:
        q = q.filter(FinancialReport.report_type == report_type)
    if country_code:
        q = q.filter(FinancialReport.country_code == country_code)
    return q.limit(limit).all()

