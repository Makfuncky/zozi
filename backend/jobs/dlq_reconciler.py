"""Periodic DLQ reconciler for ``analytics.event_dead_letter``.

Wires to the Valkey DLQ list (``event_dead_letter``) maintained by
``infrastructure.messaging.events.event_bus``.  On each run the task:

1. Reads the Valkey DLQ list length.
2. Emits a Prometheus alert if the backlog exceeds ``DLQ_BACKLOG_ALERT_THRESHOLD``.
3. Optionally persists the full DLQ payload batch to the Postgres
   ``analytics.event_dead_letter`` table so that governance dashboards can
   surface DLQ entries without depending on Valkey uptime.

Run frequency
-------------
Scheduled via Celery Beat (see ``jobs/periodic_tasks.py``).  Default cadence
is every 5 minutes; tune via the ``DLQ_RECONCILIATION_INTERVAL`` env var.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from celery import shared_task
from jobs.celery_app import celery_app

logger = logging.getLogger(__name__)

# Alert when Valkey DLQ list has more than this many entries.
DLQ_BACKLOG_ALERT_THRESHOLD: int = 100


@shared_task(
    bind=True,
    name="tasks.dlq_reconciler.run_dlq_reconciliation",
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    time_limit=300,
    soft_time_limit=240,
)
def run_dlq_reconciliation(self) -> dict[str, Any]:
    """Reconcile the Valkey DLQ list against ``analytics.event_dead_letter``.

    Returns a summary dict:
        {
            "status": "ok" | "alert" | "error",
            "dlq_depth": int,
            "persisted": int,
            "threshold": int,
        }
    """
    try:
        from datetime import datetime, timezone

        from infrastructure.messaging.events.event_bus import DLQ_KEY, _get_valkey_client
    except ImportError:
        logger.warning("DLQ reconciler: event_bus module unavailable")
        return {"status": "error", "reason": "event_bus_unavailable"}

    client = _get_valkey_client()
    if client is None or not hasattr(client, "llen"):
        logger.debug("DLQ reconciler skipped: Valkey client unavailable")
        return {"status": "ok", "dlq_depth": 0, "persisted": 0, "threshold": DLQ_BACKLOG_ALERT_THRESHOLD}

    try:
        dlq_depth: int = int(client.llen(DLQ_KEY) or 0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DLQ reconciler: failed to read DLQ depth: %s", exc)
        raise self.retry(exc=exc)

    entries: list[dict[str, Any]] = []
    if dlq_depth > 0:
        try:
            raw_entries = client.lrange(DLQ_KEY, 0, -1)
            for raw in raw_entries:
                try:
                    entries.append(json.loads(raw))
                except json.JSONDecodeError:
                    entries.append({"raw": raw, "_decode_error": True})
        except Exception as exc:  # noqa: BLE001
            logger.warning("DLQ reconciler: failed to read DLQ entries: %s", exc)
            raise self.retry(exc=exc)

    persisted = 0
    if entries:
        try:
            persisted = _persist_dlq_batch(entries)
            logger.info(
                "DLQ reconciler: persisted %d/%d DLQ entries to Postgres",
                persisted,
                len(entries),
            )
        except Exception as exc:  # noqa: BLE001 - persistence failure must not lose DLQ data
            logger.warning("DLQ reconciler: persistence failed: %s", exc, exc_info=True)

    status = "alert" if dlq_depth >= DLQ_BACKLOG_ALERT_THRESHOLD else "ok"
    if status == "alert":
        logger.warning(
            "DLQ backlog alert: depth=%d (threshold=%d). "
            "Investigate event_bus handler failures.",
            dlq_depth,
            DLQ_BACKLOG_ALERT_THRESHOLD,
        )

    return {
        "status": status,
        "dlq_depth": dlq_depth,
        "persisted": persisted,
        "threshold": DLQ_BACKLOG_ALERT_THRESHOLD,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _persist_dlq_batch(entries: list[dict[str, Any]]) -> int:
    """Persist DLQ entries to ``analytics.event_dead_letter``.

    Returns the number of rows successfully inserted.
    Uses a raw INSERT so it works without a full SQLAlchemy session setup.
    """
    try:
        from infrastructure.database.database import get_db_context
    except ImportError:
        logger.debug("DLQ persistence skipped: database module unavailable")
        return 0

    inserted = 0
    try:
        with get_db_context() as db:
            for entry in entries:
                try:
                    db.execute(
                        """
                        INSERT INTO analytics.event_dead_letter
                            (event_type, payload_json, failed_at, reason,
                             created_at, updated_at, is_deleted)
                        VALUES
                            (:event_type, :payload_json, :failed_at, :reason,
                             now(), now(), false)
                        """,
                        {
                            "event_type": entry.get("event_type", ""),
                            "payload_json": json.dumps(entry.get("payload", entry), default=str),
                            "failed_at": datetime.now(timezone.utc).isoformat(),
                            "reason": entry.get("error", entry.get("reason", "")),
                        },
                    )
                    inserted += 1
                except Exception:  # noqa: BLE001 - one bad row must not block the batch
                    logger.debug("DLQ batch: skipping unpersistable entry", exc_info=True)
            db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("DLQ persistence batch failed: %s", exc, exc_info=True)

    return inserted
