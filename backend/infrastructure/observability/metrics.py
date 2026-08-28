from prometheus_client import Counter, Histogram, Gauge, REGISTRY

def _safe_metric(cls, name, *args, **kwargs):
    """Create a metric, reusing an existing one if already registered (idempotent)."""
    try:
        return cls(name, *args, **kwargs)
    except ValueError:
        # Metric already registered in a prior import (e.g. test reload).
        # Retrieve the existing collector from the default registry.
        return REGISTRY._names_to_collectors[name]

db_query_duration_seconds = _safe_metric(
    Histogram,
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

db_connections = _safe_metric(
    Gauge,
    'db_connections',
    'Number of database connections'
)

http_requests_total = _safe_metric(
    Counter,
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = _safe_metric(
    Histogram,
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

import asyncio
import functools
import time


def time_it(func):
    """Decorator that records function execution time to Prometheus.

    Supports both synchronous and coroutine functions.
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                _record_duration(func.__name__, start)
        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            _record_duration(func.__name__, start)
    return sync_wrapper


def _record_duration(name, start):
    try:
        Histogram(
            'function_duration_seconds',
            'Duration of instrumented functions in seconds',
            ['function'],
        ).labels(function=name).observe(time.perf_counter() - start)
    except Exception:
        pass
