"""Canonical Celery worker: automated payout sweep (supplier + logistics).

Wires to ``domains.finance.services.payouts.auto_payout_scheduler``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.payout_sweep.run_payout_sweep",
    max_retries=1,
    default_retry_delay=300,
)
def run_payout_sweep(
    self,
    force_date: Optional[str] = None,
    batch_notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run auto-payout sweep for eligible supplier and logistics settlements."""
    try:
        from datetime import datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.finance.services.payouts.auto_payout_scheduler import (
            run_auto_logistics_payout_sweep,
            run_auto_payout_sweep,
        )

        db = SessionLocal()
        try:
            supplier_result = run_auto_payout_sweep(
                db, force_date=force_date, batch_notes=batch_notes, dry_run=dry_run
            )
            logistics_result = run_auto_logistics_payout_sweep(
                db, force_date=force_date, batch_notes=batch_notes, dry_run=dry_run
            )
            total_processed = supplier_result.get("processed", 0) + logistics_result.get(
                "processed", 0
            )
            logger.info(
                "Auto-payout sweep completed: suppliers=%d, logistics=%d",
                supplier_result.get("processed", 0),
                logistics_result.get("processed", 0),
            )
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "supplier_sweep": supplier_result,
                "logistics_sweep": logistics_result,
                "total_processed": total_processed,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Payout sweep task failed: %s", exc)
        raise self.retry(exc=exc)
