from __future__ import annotations
"""Treasury cash-management orchestration controller.

Routers delegate here instead of importing ``services.treasury.cash_write_service``
directly, preserving the routers -> controllers -> services circuit (CIR2).
"""
from services.treasury.cash_write_service import (
    create_cash_account,
    create_cash_transaction,
    list_cash_accounts,
    get_cash_account,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "create_cash_account",
    "create_cash_transaction",
    "list_cash_accounts",
    "get_cash_account",
]
