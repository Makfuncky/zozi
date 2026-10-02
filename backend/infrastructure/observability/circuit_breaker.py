"""Circuit breaker pattern for external service calls.

Prevents cascading failures by opening the circuit after a threshold of failures
and periodically testing recovery with a half-open probe.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import structlog

from infrastructure.observability.metrics import (
    circuit_breaker_state,
    circuit_breaker_state_changes_total,
)

logger = structlog.get_logger(__name__)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitBreakerStats",
    "CircuitBreakerRegistry",
    "CircuitState",
    "circuit_break",
    "circuit_break_with_config",
    "get_circuit_breaker",
    "get_breaker",
    "get_all_breaker_stats",
]


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    def __init__(self, name: str, state: CircuitState, recovery_timeout: float):
        self.name = name
        self.state = state
        self.recovery_timeout = recovery_timeout
        super().__init__(f"Circuit breaker '{name}' is {state.value.upper()}")


@dataclass
class CircuitBreakerStats:
    """Immutable-in-practice snapshot of a breaker's counters."""

    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    half_open_calls: int
    failure_threshold: int
    recovery_timeout: float



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
        self._lock: asyncio.Lock | None = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def success_count(self) -> int:
        return self._success_count

    def get_stats(self) -> CircuitBreakerStats:
        """Return a fresh snapshot of the breaker counters."""
        return CircuitBreakerStats(
            name=self.name,
            state=self.state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            half_open_calls=self._half_open_calls,
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
        )

    def reset(self) -> None:
        """Public reset: close the breaker and zero all counters."""
        self._reset()

    def _reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

    def _get_lock(self) -> asyncio.Lock:
        """Lazily initialize the lock to avoid deprecated get_event_loop()."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _acquire_lock(self):
        try:
            return self._get_lock()
        except RuntimeError:
            return _NullContext()

    def _before_call(self) -> None:
        """Gate the call: raise when OPEN, consume a HALF_OPEN probe slot."""
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

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Invoke ``func`` through the breaker (async-aware)."""
        if asyncio.iscoroutinefunction(func):
            return self.call_async(func, *args, **kwargs)

        self._before_call()
        try:
            result = func(*args, **kwargs)
        except self.expected_exceptions as exc:
            self._on_failure(exc)
            raise
        self._on_success()
        return result

    async def call_async(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Await ``func`` through the breaker."""
        self._before_call()
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
        except self.expected_exceptions as exc:
            self._on_failure(exc)
            raise
        self._on_success()
        return result

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                self._before_call()
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
            self._before_call()
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
                old_state = self.state.value
                self._reset()
                circuit_breaker_state.labels(service=self.name).set(0)
                circuit_breaker_state_changes_total.labels(
                    service=self.name,
                    from_state=old_state,
                    to_state=CircuitState.CLOSED.value,
                ).inc()
        else:
            self._success_count += 1
            self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self, exc: Exception) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            old_state = self.state.value
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
                circuit_breaker_state.labels(service=self.name).set(1)
                circuit_breaker_state_changes_total.labels(
                    service=self.name,
                    from_state=old_state,
                    to_state=CircuitState.OPEN.value,
                ).inc()
            else:
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
        circuit_breaker_state.labels(service=name).set(0)
    return _default_breakers[name]


def get_all_breaker_stats() -> dict[str, dict[str, Any]]:
    """Get stats for all circuit breakers for health checks."""
    for name, cb in _default_breakers.items():
        state_value = 0 if cb.state == CircuitState.CLOSED else (1 if cb.state == CircuitState.OPEN else 2)
        circuit_breaker_state.labels(service=name).set(state_value)
    return {
        name: {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
        }
        for name, cb in _default_breakers.items()
    }


get_breaker = get_circuit_breaker


class CircuitBreakerRegistry:
    """Named, self-contained collection of :class:`CircuitBreaker` instances."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[float] = None,
    ) -> CircuitBreaker:
        """Get or create a breaker scoped to this registry."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=(
                    failure_threshold
                    if failure_threshold is not None
                    else self.failure_threshold
                ),
                recovery_timeout=(
                    recovery_timeout
                    if recovery_timeout is not None
                    else self.recovery_timeout
                ),
            )
        return self._breakers[name]

    def get_all_stats(self) -> dict[str, CircuitBreakerStats]:
        return {name: cb.get_stats() for name, cb in self._breakers.items()}

    def reset_all(self) -> None:
        for cb in self._breakers.values():
            cb.reset()

    def remove_breaker(self, name: str) -> bool:
        return self._breakers.pop(name, None) is not None


def circuit_break(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    name: Optional[str] = None,
    half_open_max_calls: int = 1,
    expected_exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator factory: route a function through its own circuit breaker."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker = CircuitBreaker(
            name=name or getattr(func, "__name__", "circuit_break"),
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
            expected_exceptions=expected_exceptions,
        )

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                return await breaker.call_async(func, *args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return breaker.call(func, *args, **kwargs)

        return sync_wrapper

    return decorator


def circuit_break_with_config(config: dict):
    """``circuit_break`` driven by a plain configuration mapping."""
    cfg = dict(config or {})
    return circuit_break(
        failure_threshold=int(cfg.get("failure_threshold", 5)),
        recovery_timeout=float(cfg.get("recovery_timeout", 30.0)),
        name=cfg.get("name"),
        half_open_max_calls=int(cfg.get("half_open_max_calls", 1)),
        expected_exceptions=tuple(
            cfg.get("expected_exceptions", (Exception,))
        ),
    )
