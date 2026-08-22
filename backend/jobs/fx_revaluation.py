"""Canonical Celery worker: FX revaluation.

Wires to ``domains.comms.services.import_service.run_fx_revaluation``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.fx_revaluation.run_fx_revaluation_task",
    max_retries=1,
    default_retry_delay=300,
)
def run_fx_revaluation_task(
    self,
    as_of: Optional[str] = None,
    country_code: Optional[str] = None,
) -> dict[str, Any]:
    """Revalue open foreign-currency balances as of a given date."""
    try:
        from datetime import date, datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.comms.services.import_service import run_fx_revaluation

        as_of_date = (
            datetime.fromisoformat(as_of).date() if as_of else date.today()
        )

        db = SessionLocal()
        try:
            result = run_fx_revaluation(
                db, as_of=as_of_date, country_code=country_code
            )
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "as_of": as_of_date.isoformat(),
                "country_code": country_code,
                "result": result,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("FX revaluation task failed: %s", exc)
        raise self.retry(exc=exc)
