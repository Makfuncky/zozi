"""Migration re-export shim for the old controller module `payouts_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from domains.governance.services.logistics.flat_admin_logistics_operations_service import verify_payout_route

# Unresolved during migration: list_pending_payouts_route
