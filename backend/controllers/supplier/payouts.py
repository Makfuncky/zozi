"""Supplier payout operations.

Backward-compatible re-exports for importers that reference the old
controllers.supplier.payouts path.  Canonical implementation moved to
controllers/treasury/payouts.py (which re-exports from supplier_controller).
"""
from controllers.treasury.payouts import (  # noqa: F401
    get_payout_history,
    request_payout,
)
