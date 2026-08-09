from __future__ import annotations
"""Treasury auto-payout orchestration controller.

Routers delegate here instead of importing ``services.auto_payout_scheduler``
directly, preserving the routers -> controllers -> services circuit (CIR2).
"""
from services.auto_payout_scheduler import (
    get_background_job_status,
    start_auto_payout_background_job,
    stop_auto_payout_background_job,
    run_auto_payout_sweep,
    run_auto_logistics_payout_sweep,
    update_background_status,
)

__all__ = [
    "get_background_job_status",
    "start_auto_payout_background_job",
    "stop_auto_payout_background_job",
    "run_auto_payout_sweep",
    "run_auto_logistics_payout_sweep",
    "update_background_status",
]
