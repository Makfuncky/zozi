"""Tests for Celery app configuration: include coverage and DLQ wiring."""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

# Ensure backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("APP_ENV", "test")

from jobs.celery_app import celery_app  # noqa: E402

# All job modules present in backend/jobs/ (excluding __init__.py and celery_app.py)
_JOB_MODULES = [
    "jobs.ai_tasks",
    "jobs.periodic_tasks",
    "jobs.payout_tasks",
    "jobs.email_tasks",
    "jobs.fraud_monitoring",
    "jobs.ghost_order_detector",
    "jobs.data_retention",
    "jobs.payroll_run",
    "jobs.payout_sweep",
    "jobs.reconciliation_cron",
    "jobs.bank_statement_importer",
    "jobs.fx_revaluation",
    "jobs.accrual_reversal",
    "jobs.background_tasks",
    "jobs.video_tasks",
    "jobs.threat_feed_updater",
    "jobs.ml_worker",
    "jobs.mcp_server",
    "jobs.mcp_marketplace_server",
    "jobs.async_workers",
]


def test_include_covers_all_job_modules():
    """All job modules discovered in backend/jobs/ must be in the Celery include list."""
    include_set = set(celery_app.conf.include)
    for module in _JOB_MODULES:
        assert module in include_set, f"Job module {module} is missing from include list"


def test_dlq_configured():
    """Dead-letter queue and exchange must be configured for failed tasks."""
    queues = celery_app.conf.task_queues
    assert queues is not None, "task_queues is not configured"

    queue_names = {q.name for q in queues}
    assert "dlq" in queue_names, "Dead-letter queue 'dlq' is not configured"

    dlq_found = False
    for q in queues:
        if q.name == "dlq":
            dlq_found = True
            assert q.exchange is not None, "DLQ exchange is not configured"
            assert q.exchange.name == "dlx", f"DLQ exchange name is {q.exchange.name}, expected 'dlx'"
            break
    assert dlq_found, "DLQ queue definition not found in task_queues"

    for q in queues:
        if q.name == "dlq":
            continue
        args = q.queue_arguments or {}
        assert args.get("x-dead-letter-exchange") == "dlx", (
            f"Queue {q.name} is missing x-dead-letter-exchange routing to dlx"
        )
        assert args.get("x-dead-letter-routing-key") == "dlq", (
            f"Queue {q.name} is missing x-dead-letter-routing-key routing to dlq"
        )
