"""Finance domain — accounting creation services.

Moved from domains/governance/services/finance/ (wrong location).
Provides journal entry, period close, and sub-ledger operations.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.finance.ports import (
    FinancialReportingService,
    get_or_create_fiscal_period,
    get_current_fiscal_period,
    close_period,
    list_periods,
    reverse_journal_entry,
    generate_forecast,
    controller_get_ar_summary,
    controller_get_ap_summary,
    controller_post_ar_invoice,
    controller_post_ar_payment,
    controller_post_ap_payable,
    controller_post_ap_payment,
)


def get_fiscal_period(db: Session, country_code: str, period_year: int, period_month: int):
    """Get or create a fiscal period for the given country and date."""
    return get_or_create_fiscal_period(db, country_code, period_year, period_month)


def get_current_period(db: Session, country_code: str):
    """Get the current open fiscal period for a country."""
    return get_current_fiscal_period(db, country_code)


def close_fiscal_period(db: Session, period_id: int, notes: Optional[str] = None,
                        transfer_to_retained_earnings: bool = True):
    """Close a fiscal period."""
    return close_period(db, period_id, notes=notes,
                        transfer_to_retained_earnings=transfer_to_retained_earnings)


def list_fiscal_periods(db: Session, country_code: str, limit: int = 50):
    """List fiscal periods for a country."""
    return list_periods(db, country_code, limit)


def reverse_journal_entry_service(db: Session, entry_id: int, reason: str, reversed_by: Optional[int] = None):
    """Reverse a journal entry."""
    return reverse_journal_entry(db, entry_id, reason, reversed_by=reversed_by)


def generate_cash_forecast(db: Session, country_code: str, periods: int = 3):
    """Generate cash flow forecast."""
    return generate_forecast(db, country_code, periods)


def get_ar_summary(db: Session, customer_id: int):
    """Get accounts receivable summary for a customer."""
    return controller_get_ar_summary(db, customer_id)


def get_ap_summary(db: Session, supplier_id: int):
    """Get accounts payable summary for a supplier."""
    return controller_get_ap_summary(db, supplier_id)


def post_ar_invoice(db: Session, customer_id: int, amount: Decimal, **kwargs):
    """Post an AR invoice."""
    return controller_post_ar_invoice(db, customer_id, amount, **kwargs)


def post_ar_payment(db: Session, customer_id: int, amount: Decimal, **kwargs):
    """Post an AR payment."""
    return controller_post_ar_payment(db, customer_id, amount, **kwargs)


def post_ap_payable(db: Session, supplier_id: int, amount: Decimal, **kwargs):
    """Post an AP payable."""
    return controller_post_ap_payable(db, supplier_id, amount, **kwargs)


def post_ap_payment(db: Session, supplier_id: int, amount: Decimal, **kwargs):
    """Post an AP payment."""
    return controller_post_ap_payment(db, supplier_id, amount, **kwargs)
