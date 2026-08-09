"""Treasury service facade.

Re-exports the canonical treasury read helpers from the query service so the
controller layer has a single import surface (CIR2).
"""
from __future__ import annotations

from services.treasury.treasury_query_service import (
    get_cash_position,
    get_supplier_payables,
    get_treasury_metrics,
    get_vat_liability,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "get_treasury_metrics",
    "get_cash_position",
    "get_vat_liability",
    "get_supplier_payables",
]
