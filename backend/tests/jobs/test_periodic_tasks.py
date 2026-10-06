"""Tests for periodic task wiring: retry backoff and time limits."""
from __future__ import annotations

import os

os.environ["SECRET_KEY"] = "a" * 32

import jobs.periodic_tasks  # noqa: F401
from jobs.celery_app import celery_app  # noqa: E402

PERIODIC_TASK_NAMES = [
    "tasks.periodic_tasks.run_auto_payout_sweep",
    "tasks.periodic_tasks.run_finance_reconciliation",
    "tasks.periodic_tasks.compute_vat_remittance",
    "tasks.periodic_tasks.generate_supplier_statements",
    "tasks.periodic_tasks.generate_distributor_statements",
    "tasks.periodic_tasks.run_alert_engine",
    "tasks.periodic_tasks.cleanup_old_jobs",
    "tasks.periodic_tasks.cleanup_expired_tokens",
    "tasks.periodic_tasks.health_check",
]

RETRY_BACKOFF_TASK_NAMES = [
    name for name in PERIODIC_TASK_NAMES
    if name not in (
        "tasks.periodic_tasks.health_check",
        "tasks.periodic_tasks.cleanup_expired_tokens",
    )
]


def test_time_limits_set():
    for name in PERIODIC_TASK_NAMES:
        task = celery_app.tasks.get(name)
        assert task is not None, f"Task {name} not found"
        assert task.time_limit is not None, f"Task {name} missing time_limit"
        assert task.soft_time_limit is not None, f"Task {name} missing soft_time_limit"


def test_retry_backoff():
    for name in RETRY_BACKOFF_TASK_NAMES:
        task = celery_app.tasks.get(name)
        assert task is not None, f"Task {name} not found"
        assert getattr(task, "retry_backoff", False) is True
        assert getattr(task, "retry_jitter", False) is True
        assert getattr(task, "retry_backoff_max", None) is not None
