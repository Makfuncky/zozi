"""Test payout retry backoff and jitter behavior (WIR-011)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend package root is importable.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "a" * 64)

# Celery 5.5 removed app.signals; patch for backward-compatible modules.
from celery import Celery as _Celery

if not hasattr(_Celery, "signals"):
    class _FakeSignal:
        @staticmethod
        def connect(fn):
            return fn

    class _FakeSignals:
        worker_init = _FakeSignal()
        worker_shutdown = _FakeSignal()

    _Celery.signals = _FakeSignals()

from jobs.celery_app import celery_app  # noqa: E402
import jobs.payout_tasks  # noqa: F401


def test_payout_retry_backoff_and_jitter():
    """Verify exponential backoff with jitter is configured on payout tasks."""
    task_names = [
        "tasks.payout_tasks.dispatch_payout_batch",
        "tasks.payout_tasks.process_individual_payout",
        "tasks.payout_tasks.retry_failed_payouts",
    ]
    for name in task_names:
        task = celery_app.tasks.get(name)
        assert task is not None, f"Task {name} not found in Celery app"
        assert getattr(task, "retry_backoff", False) is True, (
            f"{name}: retry_backoff must be True"
        )
        assert getattr(task, "retry_jitter", False) is True, (
            f"{name}: retry_jitter must be True"
        )
        assert getattr(task, "retry_backoff_max", None) is not None, (
            f"{name}: retry_backoff_max must be set"
        )
