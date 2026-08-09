from __future__ import annotations
"""Treasury payout-approval orchestration controller.

Routers delegate here instead of importing
``services.treasury.treasury_router_service`` directly, preserving the
routers -> controllers -> services circuit (CIR2).
"""
from services.treasury.treasury_router_service import (
    get_pending_payouts,
    approve_payout,
    reject_payout,
    approve_batch,
    reject_batch,
    dispatch_batch,
)

__all__ = [
    "get_pending_payouts",
    "approve_payout",
    "reject_payout",
    "approve_batch",
    "reject_batch",
    "dispatch_batch",
]
