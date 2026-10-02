from __future__ import annotations

import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_call(
    func: Callable[..., T],
    *args: Any,
    attempts: int = 3,
    delay: float = 2.0,
    return_attempt: bool = False,
    **kwargs: Any,
) -> T | tuple[T, int]:
    """Call *func* with retry logic.

    Retries up to ``attempts`` times with ``delay`` seconds between attempts.
    Returns the result of the successful call, or raises the last exception.
    When ``return_attempt`` is ``True``, returns a ``(result, attempt)`` tuple.
    """
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = func(*args, **kwargs)
            if return_attempt:
                return result, attempt  # type: ignore[return-value]
            return result
        except Exception as exc:
            last_exc = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, attempts, exc)
            if attempt < attempts:
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]
