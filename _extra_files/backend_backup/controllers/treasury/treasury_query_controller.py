from __future__ import annotations
"""Finance treasury-query orchestration controller.

The treasury API router delegates here instead of importing
``services.treasury.treasury_query_service`` directly, preserving the
routers -> controllers -> services circuit (CIR2).
"""
from services.treasury.treasury_query_service import (
    calculate_eosb,
    create_journal_entry,
    create_treasury_transaction,
    get_account_balance,
    get_cash_flow_forecast,
    get_cash_position,
    get_payment_transactions,
    get_payroll_summary,
    get_supplier_payables,
    get_treasury_account,
    get_treasury_ledger,
    get_treasury_metrics,
    get_trial_balance,
    get_vat_liability,
)

__all__ = [
    "calculate_eosb",
    "create_journal_entry",
    "create_treasury_transaction",
    "get_account_balance",
    "get_cash_flow_forecast",
    "get_cash_position",
    "get_payment_transactions",
    "get_payroll_summary",
    "get_supplier_payables",
    "get_treasury_account",
    "get_treasury_ledger",
    "get_treasury_metrics",
    "get_trial_balance",
    "get_vat_liability",
]
