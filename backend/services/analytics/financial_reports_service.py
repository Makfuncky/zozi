"""Financial reports service (analytics).

Imported by ``services._registry`` so its report builders register at app
startup. Kept dependency-light to avoid import-time side effects.
"""
from __future__ import annotations

import logging
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)
