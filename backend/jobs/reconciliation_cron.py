"""Canonical Celery worker: finance reconciliation cron.

Wires to ``domains.finance.services.treasury.cash_management_service.run_scheduled_reconciliation_cycle``.
"""
from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.reconciliation_cron.run_reconciliation_cron",
    max_retries=1,
    default_retry_delay=300,
)
def run_reconciliation_cron(self) -> dict[str, Any]:
    """Run the daily finance reconciliation pass (bank transaction auto-match)."""
    try:
        from datetime import datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.finance.services.treasury.cash_management_service import (
            run_scheduled_reconciliation_cycle,
        )

        db = SessionLocal()
        try:
            result = run_scheduled_reconciliation_cycle(db)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Reconciliation cron task failed: %s", exc)
        raise self.retry(exc=exc)
