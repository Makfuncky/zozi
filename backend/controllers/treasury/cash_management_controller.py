"""
Cash Management Controller — backward-compatibility re-export shim.

The actual implementation now lives in services/cash_management_service.py
(correct layer: services). This file re-exports for legacy importers.
"""
from services.cash_management_service import *  # noqa: F401, F403

__all__ = [
    "get_cash_position",
    "get_cash_flow_projection",
    "reconcile_cash",
    "record_cash_transaction",
]
