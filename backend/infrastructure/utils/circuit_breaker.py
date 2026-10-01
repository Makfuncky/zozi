from infrastructure.observability.circuit_breaker import *  # noqa: F401,F403

import asyncio
import time
from typing import Any, Callable, Tuple


class CircuitBreakerWithRetry:
    """Circuit breaker with built-in retry logic."""

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
        from infrastructure.observability.circuit_breaker import (
            CircuitBreaker,
        )
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
        if asyncio.iscoroutinefunction(func):
            return asyncio.run(self._async_wrapper(func, *args, **kwargs))
        return self._sync_wrapper(func, *args, **kwargs)

    def _sync_wrapper(self, func: Callable, *args, **kwargs) -> Any:
        for attempt in range(self.retry_count + 1):
            try:
                return self._breaker.call(func, *args, **kwargs)
            except Exception:
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay * (self.retry_backoff ** attempt))
                else:
                    raise

    async def _async_wrapper(self, func: Callable, *args, **kwargs) -> Any:
        for attempt in range(self.retry_count + 1):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception:
                if attempt < self.retry_count:
                    await asyncio.sleep(
                        self.retry_delay * (self.retry_backoff ** attempt)
                    )
                else:
                    raise


def retry(
    func: Callable,
    retries: int = 2,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    if asyncio.iscoroutinefunction(func):
        return asyncio.run(_async_retry(func, retries, delay, backoff, exceptions))
    return _sync_retry(func, retries, delay, backoff, exceptions)


def _sync_retry(
    func: Callable, retries: int, delay: float, backoff: float, exceptions: tuple
) -> Any:
    for attempt in range(retries + 1):
        try:
            return func()
        except exceptions:
            if attempt < retries:
                time.sleep(delay * (backoff ** attempt))
            else:
                raise


async def _async_retry(
    func: Callable, retries: int, delay: float, backoff: float, exceptions: tuple
) -> Any:
    for attempt in range(retries + 1):
        try:
            result = func()
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except exceptions:
            if attempt < retries:
                await asyncio.sleep(delay * (backoff ** attempt))
            else:
                raise
