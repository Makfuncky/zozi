"""Async service wrappers for hot-path domains.

Provides async wrappers around synchronous domain services so that
FastAPI route handlers can run blocking DB queries in a thread pool
without blocking the event loop. This is critical for handling 100K+
concurrent users where blocking the event loop starves other requests.

Usage:
    async def get_products(category: str, db: Session = Depends(get_db)):
        return await run_async(list_products, category, db)

    async def get_country(code: str, db: Session = Depends(get_db)):
        return await run_async(get_public_country_config, code, db)
"""
from __future__ import annotations

import asyncio
import functools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Dedicated thread pool for DB-bound operations.
# Sized to match the connection pool: pool_size + max_overflow = 50 max concurrent DB ops.
# Using a module-level executor avoids spawning threads per-request.
_db_executor = ThreadPoolExecutor(
    max_workers=32,
    thread_name_prefix="zozi-db-async",
)


def run_async(func: Callable[..., T], *args: Any, **kwargs: Any) -> Coroutine[Any, Any, T]:
    """Run a synchronous function in the dedicated DB thread pool.

    This prevents blocking the asyncio event loop during DB I/O,
    allowing the server to process other requests concurrently.
    """
    loop = asyncio.get_event_loop()
    if kwargs:
        func = functools.partial(func, **kwargs)
    return loop.run_in_executor(_db_executor, func, *args)


def shutdown_executor() -> None:
    """Gracefully shut down the thread pool executor."""
    global _db_executor
    _db_executor.shutdown(wait=False, cancel_futures=True)
    logger.info("DB async executor shut down")
