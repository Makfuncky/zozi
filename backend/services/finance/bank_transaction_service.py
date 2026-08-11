"""Bank transaction service.

Imported by ``services.common._registry`` so its handlers/parsers register at app
startup. Kept dependency-light to avoid import-time side effects.
"""
from __future__ import annotations

import logging
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)
