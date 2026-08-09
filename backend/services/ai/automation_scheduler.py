"""Automation scheduler service.

Imported by ``services._registry`` so its scheduled jobs register at app
startup. Kept dependency-light to avoid import-time side effects.
"""
from __future__ import annotations

import logging
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def register_automation_jobs() -> None:
    """Register scheduled automation jobs (placeholder)."""
    logger.debug("Automation scheduler jobs registered")
