from __future__ import annotations
"""Treasury payout-admin orchestration controller.

Routers delegate here instead of importing
``services.treasury.payout_admin_service`` directly, preserving the
routers -> controllers -> services circuit (CIR2).
"""
from services.treasury.payout_admin_service import (
    query_payouts_by_country,
    query_pending_payouts,
    query_pending_payouts_by_country,
    get_payout,
    create_payout_record,
    verify_payout_record,
    process_payout_record,
    query_recent_automation_logs,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "query_payouts_by_country",
    "query_pending_payouts",
    "query_pending_payouts_by_country",
    "get_payout",
    "create_payout_record",
    "verify_payout_record",
    "process_payout_record",
    "query_recent_automation_logs",
]
