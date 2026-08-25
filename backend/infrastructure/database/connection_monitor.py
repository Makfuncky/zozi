"""Database connection pool monitoring and leak prevention.

Provides utilities to detect and prevent connection leaks,
monitor pool usage, and enforce timeouts on database operations.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional

from infrastructure.database.database import get_pool_metrics, get_service_session
from infrastructure.observability.metrics import db_connections

logger = logging.getLogger(__name__)


@contextmanager
def monitored_session(timeout_seconds: int = 30) -> Generator[Any, None, None]:
    """Context manager that monitors a database session for leaks.

    Automatically tracks session duration and warns if it exceeds timeout.
    Ensures the session is always closed even if an exception occurs.

    Usage:
        with monitored_session(timeout_seconds=10) as db:
            results = db.query(Model).all()
    """
    start_time = time.monotonic()
    db = None
    try:
        db = get_service_session(timeout_seconds=timeout_seconds)
        yield db.__enter__()
        db.__exit__(None, None, None)
    except Exception as exc:
        if db is not None:
            try:
                db.__exit__(type(exc), exc, exc.__traceback__)
            except Exception:
                pass
        raise
    finally:
        elapsed = time.monotonic() - start_time
        if elapsed > timeout_seconds:
            logger.warning(
                "session_timeout_exceeded",
                elapsed_seconds=round(elapsed, 2),
                timeout_seconds=timeout_seconds,
            )
        _update_connection_metrics()


def _update_connection_metrics() -> None:
    """Update Prometheus gauge with current connection pool metrics."""
    try:
        metrics = get_pool_metrics()
        if metrics and "size" in metrics:
            db_connections.set(metrics["size"])
    except Exception:
        pass


def get_connection_leak_report() -> dict[str, Any]:
    """Generate a report of potential connection leaks based on pool metrics."""
    metrics = get_pool_metrics()
    size = metrics.get("size", 1)
    checkedout = metrics.get("checkedout", 0)
    overflow = metrics.get("overflow", 0)

    utilization = checkedout / size if size > 0 else 0
    potential_leak = utilization > 0.8 and overflow > 0

    if potential_leak:
        logger.warning(
            "potential_connection_leak_detected",
            utilization=round(utilization, 2),
            checkedout=checkedout,
            pool_size=size,
            overflow=overflow,
        )

    return {
        "pool_size": size,
        "checked_out": checkedout,
        "overflow": overflow,
        "utilization": round(utilization, 2),
        "potential_leak": potential_leak,
        "recommendation": (
            "Investigate long-running queries or unclosed sessions"
            if potential_leak
            else "Pool healthy"
        ),
    }


def assert_no_leak(threshold: float = 0.8) -> None:
    """Assert that connection pool utilization is below threshold.

    Raises RuntimeError if utilization exceeds threshold, indicating
    a likely connection leak.
    """
    report = get_connection_leak_report()
    if report["utilization"] > threshold:
        raise RuntimeError(
            f"Connection pool utilization ({report['utilization']:.0%}) "
            f"exceeds threshold ({threshold:.0%}). "
            f"{report['recommendation']}"
        )


class ConnectionPoolMonitor:
    """Background monitor that periodically checks pool health.

    Usage:
        monitor = ConnectionPoolMonitor(check_interval=60)
        monitor.start()
        # ... application runs ...
        monitor.stop()
    """

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self._running = False
        self._check_count = 0
        self._alert_count = 0

    def start(self) -> None:
        """Start the background monitor (non-blocking)."""
        import threading

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("connection_pool_monitor_started", interval=self.check_interval)

    def stop(self) -> None:
        """Stop the background monitor."""
        self._running = False
        logger.info(
            "connection_pool_monitor_stopped",
            checks=self._check_count,
            alerts=self._alert_count,
        )

    def _monitor_loop(self) -> None:
        import time

        while self._running:
            try:
                self._check_count += 1
                report = get_connection_leak_report()
                if report["potential_leak"]:
                    self._alert_count += 1
            except Exception as exc:
                logger.error("pool_monitor_error", error=str(exc))
            time.sleep(self.check_interval)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "check_count": self._check_count,
            "alert_count": self._alert_count,
            "check_interval": self.check_interval,
        }
