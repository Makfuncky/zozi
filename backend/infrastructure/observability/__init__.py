"""Observability infrastructure for the ZOZI platform.

Provides structured logging with correlation IDs, Prometheus metrics,
circuit breakers, retry logic, and connection pool monitoring.
"""
from infrastructure.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    get_breaker as get_circuit_breaker,
)
from infrastructure.utils.circuit_breaker import (
    CircuitBreaker as _CircuitBreaker,
    CircuitBreakerError as _CircuitBreakerError,
)
from infrastructure.observability.retry import RetryExhausted, with_retry
from infrastructure.observability.service_observability import (
    db_query_timer,
    generate_correlation_id,
    get_correlation_id,
    instrument_service,
    log_service_call,
    log_service_error,
    request_context,
    set_context_user,
)


def get_all_breaker_stats():
    """Get stats for all circuit breakers for health checks."""
    from infrastructure.utils.circuit_breaker import CircuitBreakerRegistry
    return CircuitBreakerRegistry().get_all_stats()
