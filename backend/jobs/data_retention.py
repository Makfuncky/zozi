"""Canonical Celery worker: data retention / operational lifecycle sweeps.

Replaces ad-hoc retention logic. Calls domain services lazily so this module
imports with zero upward edges (jobs -> domains only inside the task body).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.data_retention.run_data_retention",
    max_retries=1,
    default_retry_delay=300,
    time_limit=1800,
    soft_time_limit=1500,
)
def run_data_retention(self) -> dict[str, Any]:
    """Run the operational customer retention cycle (churn / lifecycle sweeps)."""
    try:
        from datetime import datetime, timezone

        from infrastructure.database.database import SessionLocal
        from domains.governance.services.audit import (
            run_operational_retention_cycle,
        )

        db = SessionLocal()
        try:
            result = run_operational_retention_cycle(db)
            return {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Data retention task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="tasks.data_retention.cleanup_expired_tokens",
    max_retries=0,
    time_limit=300,
    soft_time_limit=240,
)
def cleanup_expired_tokens(self) -> dict[str, Any]:
    """Clean up expired JWT tokens from the Valkey blacklist."""
    try:
        from datetime import datetime, timezone

        from infrastructure.valkey.client import valkey_client

        client = valkey_client()
        if not client:
            return {"status": "skipped", "reason": "Valkey unavailable"}
        return {
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Valkey TTL handles expiration automatically",
        }
    except Exception as exc:
        logger.exception("Cleanup expired tokens task failed: %s", exc)
        return {"status": "error", "error": str(exc)}
