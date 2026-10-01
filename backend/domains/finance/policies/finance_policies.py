"""Finance authorization policies."""
from __future__ import annotations


class FinancePolicy:
    """Authorization policies for finance operations."""

    @staticmethod
    def can_view_finance(actor: dict) -> bool:
        """Check if actor can view finance data."""
        return actor.get("role") in ("admin", "super_admin", "finance")

    @staticmethod
    def can_create_invoice(actor: dict) -> bool:
        """Check if actor can create invoices."""
        return actor.get("role") in ("admin", "super_admin", "finance")

    @staticmethod
    def can_process_payout(actor: dict) -> bool:
        """Check if actor can process payouts."""
        return actor.get("role") in ("admin", "super_admin")
