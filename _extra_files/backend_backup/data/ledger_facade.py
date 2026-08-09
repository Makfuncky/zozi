"""Public facade for the General Ledger service.

Re-exports the journal/ledger API so other domains (finance, treasury, cash
management) can depend on ``data.ledger_facade`` (a cross-cutting, exempt
layer) instead of importing ``services.finance.general_ledger_service`` directly. This
keeps the backend dependency graph acyclic and satisfies the bounded-context
ownership contract enforced by the architecture auditor.
"""
from __future__ import annotations

from services.finance.general_ledger_service import (
    create_journal_entry,
    get_account_by_code,
    get_journal_entry,
    get_trial_balance,
    post_order_payment_journal,
    seed_chart_of_accounts,
)

__all__ = [
    "create_journal_entry",
    "get_account_by_code",
    "get_journal_entry",
    "get_trial_balance",
    "post_order_payment_journal",
    "seed_chart_of_accounts",
]
