"""Canonical Celery worker: payroll batch processing.

Wires to ``domains.governance.services.payroll_service.process_payroll_batch``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from celery import shared_task
from infrastructure.utils.config import settings
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.payroll_run.run_payroll_batch",
    max_retries=1,
    default_retry_delay=300,
    time_limit=1800,
    soft_time_limit=1500,
)
def run_payroll_batch(
    self,
    country_code: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Run a monthly payroll batch for a country.

    Args:
        country_code: ISO country code owning the payroll. Defaults to
            ``settings.default_country`` when omitted.
        month: Calendar month (1-12). Defaults to the current month when
            omitted.
        year: Calendar year. Defaults to the current year when omitted.
        current_user_id: Admin/user who triggered the run.
    """
    if country_code is None:
        country_code = settings.default_country
    if month is None or year is None:
        now = datetime.now(timezone.utc)
        month = month if month is not None else now.month
        year = year if year is not None else now.year

    try:
        from infrastructure.database.database import SessionLocal
        from domains.hr.payroll_service import process_payroll_batch

        db = SessionLocal()
        try:
            current_user = {"id": current_user_id} if current_user_id else {}
            result = process_payroll_batch(
                country_code, month, year, db, current_user
            )
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "country_code": country_code,
                "month": month,
                "year": year,
                "result": result,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Payroll batch task failed: %s", exc)
        raise self.retry(exc=exc)
