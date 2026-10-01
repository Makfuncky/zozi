"""Shared fixtures and patches for jobs tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend package root is importable regardless of cwd.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "a" * 64)

# Celery 5.5 removed app.signals; patch Celery class so modules that still
# use @celery_app.signals.xxx.connect can be imported during tests.
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
