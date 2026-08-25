"""Controller seam for finance read endpoints.

Thin re-export so ``routers/finance.py`` can reach the aggregation logic in
``services/finance/finance_read_service.py`` without importing ``services``
directly. The TreasuryEngine-backed write/compute endpoints remain
delegated from the router via the engine service.
"""
from __future__ import annotations

from domains.finance.services.reporting.finance_read_service import (
    get_cash_position,
    get_dashboard_metrics,
    get_gateway_exceptions,
    get_ledger,
    get_liabilities_exposure,
    get_payout_batches,
    get_supplier_earnings_report,
    get_vat_liability,
)

__all__ = [
    "get_dashboard_metrics",
    "get_ledger",
    "get_payout_batches",
    "get_cash_position",
    "get_liabilities_exposure",
    "get_vat_liability",
    "get_supplier_earnings_report",
    "get_gateway_exceptions",
]
