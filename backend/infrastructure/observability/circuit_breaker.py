"""Circuit breaker pattern for external service calls.

Prevents cascading failures by opening the circuit after a threshold of failures
and periodically testing recovery with a half-open probe.

This module provides a decorator-focused circuit breaker and re-exports
common symbols from ``infrastructure.utils.circuit_breaker`` for convenience.
"""
from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from infrastructure.utils.circuit_breaker import (
    CircuitBreakerError,
    CircuitBreaker as _UtilsCircuitBreaker,
    CircuitState,
    get_breaker,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Re-export common symbols from the canonical utils location
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitState",
    "get_circuit_breaker",
    "get_all_breaker_stats",
]


class CircuitBreaker:
    """Circuit breaker for external service calls with automatic recovery probing.

    Usage:
        cb = CircuitBreaker("stripe", failure_threshold=5, recovery_timeout=30)

        @cb
        async def call_stripe():
            ...
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

    async def _acquire_lock(self):
        if self._lock is None:
            try:
                self._lock = asyncio.Lock()
            except RuntimeError:
                return _NullContext()
        return self._lock

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                current_state = self.state

                if current_state == CircuitState.OPEN:
                    raise CircuitBreakerError(
                        self.name, CircuitState.OPEN, self.recovery_timeout
                    )

                if current_state == CircuitState.HALF_OPEN:
                    if self._half_open_calls >= self.half_open_max_calls:
                        raise CircuitBreakerError(
                            self.name, CircuitState.HALF_OPEN, self.recovery_timeout
                        )
                    self._half_open_calls += 1

                try:
                    result = await func(*args, **kwargs)
                    self._on_success()
                    return result
                except self.expected_exceptions as exc:
                    self._on_failure(exc)
                    raise

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    self.name, CircuitState.OPEN, self.recovery_timeout
                )

            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        self.name, CircuitState.HALF_OPEN, self.recovery_timeout
                    )
                self._half_open_calls += 1

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exceptions as exc:
                self._on_failure(exc)
                raise

        return sync_wrapper

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_calls:
                logger.info(
                    "circuit_breaker_closed",
                    service=self.name,
                    previous_state=CircuitState.HALF_OPEN.value,
                )
                self._reset()
        else:
            self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self, exc: Exception) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.warning(
                    "circuit_breaker_opened",
                    service=self.name,
                    failure_count=self._failure_count,
                    last_error=str(exc),
                )
            self._state = CircuitState.OPEN
            self._half_open_calls = 0
            self._success_count = 0


class _NullContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


_default_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
) -> CircuitBreaker:
    """Get or create a named circuit breaker (singleton per name)."""
    if name not in _default_breakers:
        _default_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _default_breakers[name]


def get_all_breaker_stats() -> dict[str, dict[str, Any]]:
    """Get stats for all circuit breakers for health checks."""
    return {
        name: {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
        }
        for name, cb in _default_breakers.items()
    }
