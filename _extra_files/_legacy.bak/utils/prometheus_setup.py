"""
Prometheus metrics instrumentation for Zozi API.
Exposes /metrics endpoint and auto-instruments FastAPI endpoints.
"""
from __future__ import annotations

from fastapi import FastAPI
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

from utils.config import settings


def setup_prometheus(app: FastAPI):
    if not HAS_PROMETHEUS:
        return None
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        env_var_name="PROMETHEUS_ENABLED",
    )

    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return instrumentator
