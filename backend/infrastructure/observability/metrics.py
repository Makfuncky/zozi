from prometheus_fastapi_instrumentator.metrics import Counter, Histogram
from prometheus_fastapi_instrumentator.middleware import Gauge

_metric_cache = {}

def _safe_metric(cls, name, *args, **kwargs):
    """Create a metric, reusing an existing one if already registered (idempotent)."""
    if name in _metric_cache:
        return _metric_cache[name]
    metric = cls(name, *args, **kwargs)
    _metric_cache[name] = metric
    return metric

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
import logging
import time

logger = logging.getLogger(__name__)

# OBS-005: Module-level Histogram so it is created once and reused.
# Creating a new Histogram on every call silently fails after the first
# because Prometheus rejects duplicate metric names.
function_duration_seconds = _safe_metric(
    Histogram,
    'function_duration_seconds',
    'Duration of instrumented functions in seconds',
    ['function']
)

# OBS-109: Circuit breaker state exported as Prometheus metrics.
circuit_breaker_state = _safe_metric(
    Gauge,
    'circuit_breaker_state',
    'Current state of circuit breakers (0=closed, 1=open, 2=half-open)',
    ['service']
)

circuit_breaker_state_changes_total = _safe_metric(
    Counter,
    'circuit_breaker_state_changes_total',
    'Total circuit breaker state transitions',
    ['service', 'from_state', 'to_state']
)

# OBS-111: Business metrics for checkout, payment, order creation, payout.
checkout_total = _safe_metric(
    Counter,
    'checkout_total',
    'Total checkout attempts',
    ['status']
)

checkout_duration_seconds = _safe_metric(
    Histogram,
    'checkout_duration_seconds',
    'Checkout duration in seconds',
    ['status']
)

payment_total = _safe_metric(
    Counter,
    'payment_total',
    'Total payment attempts',
    ['status', 'method']
)

payment_duration_seconds = _safe_metric(
    Histogram,
    'payment_duration_seconds',
    'Payment processing duration in seconds',
    ['method']
)

order_creation_total = _safe_metric(
    Counter,
    'order_creation_total',
    'Total order creation attempts',
    ['status']
)

order_creation_duration_seconds = _safe_metric(
    Histogram,
    'order_creation_duration_seconds',
    'Order creation duration in seconds'
)

payout_total = _safe_metric(
    Counter,
    'payout_total',
    'Total payout attempts',
    ['status']
)

payout_duration_seconds = _safe_metric(
    Histogram,
    'payout_duration_seconds',
    'Payout processing duration in seconds'
)


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
    # OBS-005: Uses module-level function_duration_seconds Histogram (created once).
    # OBS-009: Logs failure instead of bare except: pass so init errors are visible.
    try:
        function_duration_seconds.labels(function=name).observe(
            time.perf_counter() - start
        )
    except Exception as e:
        logger.warning(
            "Failed to record function_duration_seconds for %s: %s", name, e
        )
