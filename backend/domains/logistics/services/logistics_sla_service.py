"""Logistics SLA / treasury sync background job.

``run_treasury_sync`` is invoked by the APScheduler job in
``jobs.background_tasks``. It performs a best-effort reconciliation of logistics
partner settlement records against treasury; if the downstream service is
unavailable it degrades gracefully (Law 30 / Law 75) and logs a WARNING.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_treasury_sync() -> dict:
    """Reconcile logistics settlements with treasury.

    Returns a small status dict so the caller can record job outcomes without
    coupling to a specific reconciliation backend.
    """
    try:
        from infrastructure.database.database import get_db

        db = next(get_db())
        try:
            from domains.logistics.services.partners.settlement_service import reconcile_settlements

            result = reconcile_settlements(db)
            return {"status": "ok", "reconciled": result}
        finally:
            db.close()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("run_treasury_sync skipped: %s", exc)
        return {"status": "skipped", "reason": str(exc)}
