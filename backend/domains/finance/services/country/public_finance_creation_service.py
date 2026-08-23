"""Finance domain — public accounting services.

Moved from domains/governance/services/finance/ (wrong location).
Provides public-facing financial reporting and period management.
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


def get_fiscal_period_public(db: Session, country_code: str, period_year: int, period_month: int):
    """Get or create a fiscal period (public endpoint)."""
    return get_or_create_fiscal_period(db, country_code, period_year, period_month)


def get_current_period_public(db: Session, country_code: str):
    """Get the current open fiscal period (public endpoint)."""
    return get_current_fiscal_period(db, country_code)


def list_periods_public(db: Session, country_code: str, limit: int = 50):
    """List fiscal periods (public endpoint)."""
    return list_periods(db, country_code, limit)


def get_financial_report(db: Session, report_type: str, period_start: datetime,
                         period_end: datetime, country_code: Optional[str] = None):
    """Generate a financial report."""
    return FinancialReportingService.generate(
        db, report_type, period_start, period_end, country_code=country_code
    )
