"""Observability infrastructure for the ZOZI platform.

Provides structured logging with correlation IDs, Prometheus metrics,
circuit breakers, retry logic, and connection pool monitoring.
"""
from infrastructure.observability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    get_circuit_breaker,
    get_all_breaker_stats,
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
