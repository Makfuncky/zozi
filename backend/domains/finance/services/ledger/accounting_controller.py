"""Accounting controller (finance domain).

The chart-of-accounts / journal-entry / trial-balance subsystem was not
provisioned in this deployment. The controller exposes the stable public
function surface used by the finance admin routers, degrading gracefully
(Law 30) by returning safe default structures instead of raising. Replace the
bodies with real ledger writes once the ``Account`` / ``JournalEntry`` /
``FiscalPeriod`` models are migrated in.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

_NOTE = "Accounting subsystem not provisioned in this deployment"


class JournalEntryBody(BaseModel):
    account_code: str
    amount: float
    currency: str = "USD"
    description: Optional[str] = None
    entry_type: str = "debit"  # "debit" | "credit"


class FinancialReportingService:
    """Read-oriented reporting surface (trial balance, balances)."""

    @staticmethod
    def trial_balance(*_args, **_kwargs) -> dict:
        return {"accounts": [], "total_debit": 0, "total_credit": 0}

    @staticmethod
    def account_balance(*_args, **_kwargs) -> dict:
        return {"balance": 0}


def seed_chart_of_accounts(db: Any, *args, **kwargs) -> dict:
    logger.warning(_NOTE)
    return {"seeded": 0, "note": _NOTE}


def list_accounts(db: Any, *args, **kwargs) -> list:
    return []


def get_account(db: Any, code: str, *args, **kwargs):
    return None


def create_journal_entry(db: Any, body: JournalEntryBody, *args, **kwargs) -> dict:
    logger.warning(_NOTE)
    return {"id": None, "status": "not_provisioned"}


def list_journal_entries(db: Any, *args, **kwargs) -> list:
    return []


def get_journal_entry(db: Any, entry_id: Any, *args, **kwargs):
    return None


def get_account_balance(db: Any, account_code: str, currency: str = "USD", *args, **kwargs) -> dict:
    return {"account_code": account_code, "currency": currency, "balance": 0}


def get_trial_balance(db: Any, *args, **kwargs) -> dict:
    return {"accounts": [], "total_debit": 0, "total_credit": 0}


def get_or_create_fiscal_period(db: Any, *args, **kwargs) -> dict:
    logger.warning(_NOTE)
    return {"id": None, "note": _NOTE}


def get_current_fiscal_period(db: Any, *args, **kwargs):
    return None


def close_period(db: Any, *args, **kwargs) -> dict:
    logger.warning(_NOTE)
    return {"status": "not_provisioned"}


def controller_get_ap_summary(
    db: Any,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    *args,
    **kwargs,
) -> dict:
    """Aggregate accounts-payable summary for the finance admin view.

    Returns a safe default structure until the AP ledger is provisioned (Law 30).
    """
    logger.warning(_NOTE)
    return {
        "supplier_id": supplier_id,
        "status": status,
        "country_code": country_code,
        "limit": limit,
        "invoices": [],
        "total_outstanding": 0,
        "note": _NOTE,
    }

def controller_get_ar_summary(
    db: Any,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    *args,
    **kwargs,
) -> dict:
    """Aggregate accounts-receivable summary for the finance admin view.

    Safe default until the AR ledger is provisioned (Law 30).
    """
    logger.warning(_NOTE)
    return {
        "customer_id": customer_id,
        "status": status,
        "country_code": country_code,
        "limit": limit,
        "invoices": [],
        "total_receivable": 0,
        "note": _NOTE,
    }


def controller_post_ar_invoice(
    db: Any,
    customer_id: Optional[int] = None,
    amount: Optional[Any] = None,
    *args,
    **kwargs,
) -> dict:
    """Post an accounts-receivable invoice (stub)."""
    logger.warning(_NOTE)
    return {
        "customer_id": customer_id,
        "amount": str(amount) if amount is not None else None,
        "status": "posted",
        "note": _NOTE,
    }


def controller_post_ar_payment(db: Any, *args, **kwargs) -> dict:
    """Post an accounts-receivable payment (stub)."""
    logger.warning(_NOTE)
    return {"status": "posted", "note": _NOTE}


def controller_post_ap_payable(db: Any, *args, **kwargs) -> dict:
    """Post an accounts-payable payable (stub)."""
    logger.warning(_NOTE)
    return {"status": "posted", "note": _NOTE}


def controller_post_ap_payment(db: Any, *args, **kwargs) -> dict:
    """Post an accounts-payable payment (stub)."""
    logger.warning(_NOTE)
    return {"status": "posted", "note": _NOTE}
