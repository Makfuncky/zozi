"""Canonical Celery worker: accrual reversal.

Wires to ``domains.finance.services.ledger.finance_automation.reverse_accrual``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.accrual_reversal.reverse_accrual_task",
    max_retries=1,
    default_retry_delay=300,
)
def reverse_accrual_task(
    self,
    accrual_id: int,
    run_by: Optional[int] = None,
) -> dict[str, Any]:
    """Reverse a posted accrual entry.

    Args:
        accrual_id: ID of the Accrual to reverse.
        run_by: ID of the admin user performing the reversal.
    """
    try:
        from datetime import datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.finance.services.ledger.finance_automation import reverse_accrual

        db = SessionLocal()
        try:
            result = reverse_accrual(db, accrual_id, run_by=run_by)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "accrual_id": accrual_id,
                "reversed_id": getattr(result, "id", None),
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Accrual reversal task failed: %s", exc)
        raise self.retry(exc=exc)
