"""Feature atoms for finance domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the finance domain. CI must fail on any
``require_feature("finance.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "finance.invoices.read": {
        "label": "View Invoices",
        "risk": "low",
        "actions": ["read"],
        "description": "View invoices and billing records.",
    },
    "finance.invoices.manage": {
        "label": "Manage Invoices",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create, update, and manage invoices and billing records.",
    },
    "finance.payments.read": {
        "label": "View Payments",
        "risk": "low",
        "actions": ["read"],
        "description": "View payment transactions and history.",
    },
    "finance.payments.process": {
        "label": "Process Payments",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Process payment transactions and refunds through gateways.",
    },
    "finance.payouts.read": {
        "label": "View Payouts",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier and partner payout records.",
    },
    "finance.payouts.manage": {
        "label": "Manage Payouts",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Initiate, approve, and manage payouts to suppliers and partners.",
    },
    "finance.commissions.read": {
        "label": "View Commissions",
        "risk": "low",
        "actions": ["read"],
        "description": "View commission calculations and agreements.",
    },
    "finance.commissions.manage": {
        "label": "Manage Commissions",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Configure commission rates and manage commission agreements.",
    },
    "finance.general_ledger.read": {
        "label": "View General Ledger",
        "risk": "low",
        "actions": ["read"],
        "description": "View general ledger entries and accounting records.",
    },
    "finance.bank_reconciliation": {
        "label": "Bank Reconciliation",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Perform bank reconciliation and match transactions.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
