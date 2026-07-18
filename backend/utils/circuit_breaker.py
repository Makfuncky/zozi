import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Awaitable, Any, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def _is_open(self) -> bool:
        if self.state != CircuitState.OPEN:
            return False
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time < self.recovery_timeout

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self, exception: Exception):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    async def call(self, func: Callable[[], Awaitable[Any]], *args, **kwargs) -> Any:
        if self._is_open():
            raise RuntimeError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure(e)
            raise


async def retry(
    func: Callable[[], Awaitable[Any]],
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    last_exception = None
    current_delay = delay

    for attempt in range(retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < retries:
                logger.warning(
                    f"Retry {attempt + 1}/{retries} after {current_delay}s due to: {e}"
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    raise last_exception


class CircuitBreakerWithRetry:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ):
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff

    async def call(self, func: Callable[[], Awaitable[Any]], *args, **kwargs) -> Any:
        async def _wrapped():
            return await retry(
                func,
                retries=self.retry_count,
                delay=self.retry_delay,
                backoff=self.retry_backoff,
            )

        return await self.circuit_breaker.call(_wrapped, *args, **kwargs)
