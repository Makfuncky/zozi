"""Retry utilities with exponential backoff and jitter."""
from __future__ import annotations

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from infrastructure.observability.metrics import time_it

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(f"{message} (attempts={attempts}, last_error={last_exception})")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator for retrying a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first).
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Base for exponential calculation.
        jitter: Add random jitter to avoid thundering herd.
        retryable_exceptions: Tuple of exception types that trigger retry.
        on_retry: Optional callback invoked on each retry with (exception, attempt_number).
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_name = getattr(func, "__qualname__", getattr(func, "__name__", "unknown"))

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                last_exception: Optional[Exception] = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retryable_exceptions as exc:
                        last_exception = exc
                        if attempt == max_attempts:
                            break
                        delay = _calculate_delay(
                            attempt, base_delay, max_delay, exponential_base, jitter
                        )
                        logger.warning(
                            "retry_attempt",
                            function=func_name,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error=str(exc),
                        )
                        if on_retry:
                            on_retry(exc, attempt)
                        await asyncio.sleep(delay)
                raise RetryExhausted(
                    f"All {max_attempts} attempts exhausted for {func_name}",
                    last_exception=last_exception,
                    attempts=max_attempts,
                )

            return time_it(async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        break
                    delay = _calculate_delay(
                        attempt, base_delay, max_delay, exponential_base, jitter
                    )
                    logger.warning(
                        "retry_attempt",
                        function=func_name,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(exc),
                    )
                    if on_retry:
                        on_retry(exc, attempt)
                    time.sleep(delay)
            raise RetryExhausted(
                f"All {max_attempts} attempts exhausted for {func_name}",
                last_exception=last_exception,
                attempts=max_attempts,
            )

        return time_it(sync_wrapper)

    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    delay = base_delay * (exponential_base ** (attempt - 1))
    delay = min(delay, max_delay)
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    return delay
