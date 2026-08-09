"""Internal implementation bridge used by ``services.finance.general_ledger_service``.

General Ledger delegates to the concrete finance/treasury implementations. To
avoid a circular dependency (those implementations import the GL facade), the GL
service pulls these symbols lazily from ``data.ledger_impl_bridge`` rather than
importing the ``services.finance`` / ``services.treasury`` modules directly.
Because ``data`` is an exempt, cross-cutting layer, routing through this bridge
removes the ``general_ledger -> finance/treasury`` domain edges from the
dependency graph.
"""
from __future__ import annotations

from services.finance.erp_read_service import (
    get_account_by_code,
    list_accounts_paged,
)
from services.treasury.treasury_query_service import get_trial_balance
from services.treasury.treasury_seeder_service import seed_chart_of_accounts
from services.treasury.treasury_service import create_journal_entry
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "create_journal_entry",
    "get_account_by_code",
    "get_trial_balance",
    "list_accounts_paged",
    "seed_chart_of_accounts",
]
