from __future__ import annotations
"""Treasury metrics orchestration controller.

Routers delegate here instead of importing ``services.treasury.treasury_service``
directly, preserving the routers -> controllers -> services circuit (CIR2).
"""
from services.treasury.treasury_service import (
    get_treasury_metrics,
    get_cash_position,
    get_vat_liability,
    get_supplier_payables,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "get_treasury_metrics",
    "get_cash_position",
    "get_vat_liability",
    "get_supplier_payables",
]
