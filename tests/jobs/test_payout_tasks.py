"""Regression tests for payout_tasks.py retry backoff configuration.

Verifies that all payout tasks use exponential backoff with jitter (WIR-011).
"""
from __future__ import annotations

import os

os.environ["SECRET_KEY"] = "a" * 64

import jobs.payout_tasks  # noqa: F401
from jobs.celery_app import celery_app  # noqa: E402

PAYOUT_TASK_NAMES = [
    "tasks.payout_tasks.dispatch_payout_batch",
    "tasks.payout_tasks.process_individual_payout",
    "tasks.payout_tasks.retry_failed_payouts",
    "tasks.payout_tasks.health_check",
]

RETRY_BACKOFF_TASK_NAMES = [
    name for name in PAYOUT_TASK_NAMES
    if name != "tasks.payout_tasks.health_check"
]


def test_all_payout_tasks_registered():
    for name in PAYOUT_TASK_NAMES:
        task = celery_app.tasks.get(name)
        assert task is not None, f"Task {name} not found in Celery app"


def test_retry_backoff_on_retryable_tasks():
    for name in RETRY_BACKOFF_TASK_NAMES:
        task = celery_app.tasks.get(name)
        assert task is not None, f"Task {name} not found"
        assert getattr(task, "retry_backoff", False) is True, (
            f"{name}: retry_backoff must be True"
        )
        assert getattr(task, "retry_jitter", False) is True, (
            f"{name}: retry_jitter must be True"
        )
        assert getattr(task, "retry_backoff_max", None) is not None, (
            f"{name}: retry_backoff_max must be set"
        )


def test_dispatch_payout_batch_backoff_max_60():
    task = celery_app.tasks.get("tasks.payout_tasks.dispatch_payout_batch")
    assert task is not None
    assert task.retry_backoff is True
    assert task.retry_jitter is True
    assert task.retry_backoff_max == 60


def test_process_individual_payout_backoff_max_60():
    task = celery_app.tasks.get("tasks.payout_tasks.process_individual_payout")
    assert task is not None
    assert task.retry_backoff is True
    assert task.retry_jitter is True
    assert task.retry_backoff_max == 60


def test_retry_failed_payouts_backoff_max_300():
    task = celery_app.tasks.get("tasks.payout_tasks.retry_failed_payouts")
    assert task is not None
    assert task.retry_backoff is True
    assert task.retry_jitter is True
    assert task.retry_backoff_max == 300


def test_health_check_has_no_retry_backoff():
    task = celery_app.tasks.get("tasks.payout_tasks.health_check")
    assert task is not None
    assert getattr(task, "retry_backoff", False) is False
