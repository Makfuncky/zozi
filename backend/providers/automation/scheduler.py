"""Automation scheduler provider.

Centralises the APScheduler SDK so services no longer import ``apscheduler``
directly. The scheduler drives the application's periodic background jobs; the
job *definitions* remain in their owning services and are registered against
the scheduler exposed here.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    AsyncIOScheduler = None  # type: ignore[assignment]
    IntervalTrigger = None  # type: ignore[assignment]


def create_scheduler(timezone: str = "UTC") -> AsyncIOScheduler:
    """Create the application background scheduler."""
    if not HAS_APSCHEDULER:
        raise RuntimeError("APScheduler is not installed")
    return AsyncIOScheduler(timezone=timezone)


def add_interval_job(
    scheduler: AsyncIOScheduler,
    func: Callable[..., Any],
    *,
    seconds: int,
    args: Optional[List[Any]] = None,
    id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Register ``func`` to run every ``seconds`` on the given scheduler."""
    if not HAS_APSCHEDULER:
        raise RuntimeError("APScheduler is not installed")
    scheduler.add_job(
        func,
        trigger=IntervalTrigger(seconds=seconds),
        args=args or [],
        id=id,
        **kwargs,
    )


__all__ = ["AsyncIOScheduler", "IntervalTrigger", "create_scheduler", "add_interval_job", "HAS_APSCHEDULER"]
