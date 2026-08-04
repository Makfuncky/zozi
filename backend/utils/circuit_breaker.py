"""Circuit breaker implementation for Zozi backend.

Provides circuit breaker functionality for external dependencies
and service integration points.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Dict, List
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    creation_time: float = field(default_factory=time.time)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker for external service calls.

    Implements the circuit breaker pattern to prevent cascading failures
    when external services are unavailable or degraded.

    Attributes:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening
        recovery_timeout: Time in seconds before attempting to recover
        expected_exceptions: Exception types that trigger failure
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exceptions: tuple = (Exception,),
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.half_open_max_calls = half_open_max_calls

        self._stats = CircuitStats(name=name)
        self._lock = Lock()

    def _is_open(self) -> bool:
        """Check if circuit is open."""
        with self._lock:
            if self._stats.state == CircuitState.OPEN:
                if self._stats.last_failure_time is None:
                    return True

                if time.time() - self._stats.last_failure_time >= self.recovery_timeout:
                    self._stats.state = CircuitState.HALF_OPEN
                    logger.info(
                        "Circuit breaker '%s' transitioning to HALF_OPEN",
                        self.name,
                    )
                    return False

            return self._stats.state == CircuitState.OPEN

    def _on_success(self):
        """Record successful call and update state."""
        with self._lock:
            self._stats.success_count += 1
            self._stats.total_requests += 1
            self._stats.last_success_time = time.time()

            if self._stats.state == CircuitState.HALF_OPEN:
                self._stats.failure_count = 0
                self._stats.state = CircuitState.CLOSED
                logger.info(
                    "Circuit breaker '%s' transitioning to CLOSED (successful calls)",
                    self.name,
                )

    def _on_failure(self, exception: Exception):
        """Record failed call and update state."""
        with self._lock:
            self._stats.failure_count += 1
            self._stats.total_requests += 1
            self._stats.last_failure_time = time.time()

            if self._stats.failure_count >= self.failure_threshold:
                self._stats.state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker '%s' opened after %d failures",
                    self.name,
                    self._stats.failure_count,
                )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of function execution

        Raises:
            CircuitBreakerError: If circuit is open
            expected_exceptions: If function raises expected exception
        """
        if self._is_open():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise

    def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of function execution

        Raises:
            CircuitBreakerError: If circuit is open
            expected_exceptions: If function raises expected exception
        """
        if self._is_open():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )

        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                async def _wrapped():
                    try:
                        actual_result = await result
                        self._on_success()
                        return actual_result
                    except self.expected_exceptions as e:
                        self._on_failure(e)
                        raise

                return _wrapped()

            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure(e)
            raise

    def get_stats(self) -> CircuitStats:
        """Get circuit breaker statistics.

        Returns:
            CircuitBreakerStats instance
        """
        with self._lock:
            return CircuitStats(
                name=self._stats.name,
                state=self._stats.state,
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                total_requests=self._stats.total_requests,
                last_failure_time=self._stats.last_failure_time,
                last_success_time=self._stats.last_success_time,
                creation_time=self._stats.creation_time,
            )

    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._stats.state = CircuitState.CLOSED
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._stats.total_requests = 0
            logger.info("Circuit breaker '%s' reset", self.name)


def circuit_break(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple = (Exception,),
):
    """Decorator to add circuit breaker protection.

    Args:
        failure_threshold: Number of failures before opening
        recovery_timeout: Time in seconds before attempting to recover
        expected_exceptions: Exception types that trigger failure

    Returns:
        Decorated function with circuit breaker protection
    """
    from functools import wraps

    def decorator(func):
        breaker = CircuitBreaker(
            name=func.__name__,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


class CircuitBreakerRegistry:
    """Registry for managing circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker by name.

        Args:
            name: Name of the circuit breaker
            **kwargs: Additional arguments for circuit breaker creation

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name, **kwargs)
                logger.info(
                    "Created circuit breaker '%s' with kwargs: %s",
                    name,
                    kwargs,
                )

            return self._breakers[name]

    def remove_breaker(self, name: str) -> bool:
        """Remove a circuit breaker from registry.

        Args:
            name: Name of the circuit breaker to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                logger.info("Removed circuit breaker '%s'", name)
                return True

            return False

    def get_all_stats(self) -> Dict[str, CircuitStats]:
        """Get statistics for all circuit breakers.

        Returns:
            Dictionary mapping breaker names to stats
        """
        with self._lock:
            return {
                name: breaker.get_stats()
                for name, breaker in self._breakers.items()
            }

    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("Reset all circuit breakers")


# Global registry instance
_breaker_registry = CircuitBreakerRegistry()


def get_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get a circuit breaker from the global registry.

    Args:
        name: Name of the circuit breaker
        **kwargs: Additional arguments for circuit breaker creation

    Returns:
        CircuitBreaker instance
    """
    return _breaker_registry.get_breaker(name, **kwargs)


def circuit_break_with_config(config: Dict[str, Any]) -> Callable:
    """Create a circuit breaker decorator from configuration.

    Args:
        config: Circuit breaker configuration

    Returns:
        Decorator function
    """
    def decorator(func):
        breaker_name = config.get("name", func.__name__)
        return circuit_break(
            failure_threshold=config.get("failure_threshold", 5),
            recovery_timeout=config.get("recovery_timeout", 60.0),
            expected_exceptions=tuple(config.get("expected_exceptions", [Exception])),
        )(func)

    return decorator


class CircuitBreakerWithRetry:
    """Circuit breaker with built-in retry logic.

    Combines circuit breaker pattern with exponential backoff retry.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        retry_count: int = 2,
        retry_delay: float = 0.5,
        retry_backoff: float = 2.0,
        expected_exceptions: tuple = (Exception,),
    ):
        self._breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
        )
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker and retry protection."""
        if asyncio.iscoroutinefunction(func):
            return self._async_wrapper(func, *args, **kwargs)
        else:
            return self._sync_wrapper(func, *args, **kwargs)

    def _sync_wrapper(self, func: Callable, *args, **kwargs) -> Any:
        for attempt in range(self.retry_count + 1):
            try:
                return self._breaker.call(func, *args, **kwargs)
            except Exception as e:
                if attempt < self.retry_count:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    time.sleep(delay)
                else:
                    raise

    async def _async_wrapper(self, func: Callable, *args, **kwargs) -> Any:
        for attempt in range(self.retry_count + 1):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception as e:
                if attempt < self.retry_count:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise


def retry(
    func: Callable,
    retries: int = 2,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Execute function with retry logic.

    Args:
        func: Function to execute (can be sync or async)
        retries: Number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Exception types that trigger retry

    Returns:
        Result of function execution
    """
    if asyncio.iscoroutinefunction(func):
        return _async_retry(func, retries, delay, backoff, exceptions)
    else:
        return _sync_retry(func, retries, delay, backoff, exceptions)


def _sync_retry(func: Callable, retries: int, delay: float, backoff: float, exceptions: tuple) -> Any:
    for attempt in range(retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt < retries:
                wait = delay * (backoff ** attempt)
                time.sleep(wait)
            else:
                raise


async def _async_retry(func: Callable, retries: int, delay: float, backoff: float, exceptions: tuple) -> Any:
    for attempt in range(retries + 1):
        try:
            return await func()
        except exceptions as e:
            if attempt < retries:
                wait = delay * (backoff ** attempt)
                await asyncio.sleep(wait)
            else:
                raise