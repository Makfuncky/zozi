"""Canonical Celery worker: bank statement import.

Wires to ``domains.finance.services.finance_automation.import_bank_statement``.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.bank_statement_importer.import_bank_statement_task",
    max_retries=2,
    default_retry_delay=120,
)
def import_bank_statement_task(
    self,
    lines: list[dict],
    bank_name: Optional[str] = None,
    file_name: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = None,
    imported_by: Optional[int] = None,
    period_start=None,
    period_end=None,
) -> dict[str, Any]:
    """Bulk-import bank statement lines and auto-map them via mapping rules."""
    try:
        from datetime import datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.finance.services.finance_automation import import_bank_statement

        db = SessionLocal()
        try:
            result = import_bank_statement(
                db,
                lines=lines,
                bank_name=bank_name,
                file_name=file_name,
                currency=currency,
                country_code=country_code,
                imported_by=imported_by,
                period_start=period_start,
                period_end=period_end,
            )
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "import_id": getattr(result, "id", None),
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Bank statement import task failed: %s", exc)
        raise self.retry(exc=exc)
