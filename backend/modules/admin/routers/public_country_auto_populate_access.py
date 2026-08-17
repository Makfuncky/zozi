"""Public country auto-populate access layer.

Reached through the ``data.routers_country_auto_populate`` shim so first-party
layers can import it via the exempt ``data`` facade. This module owns the
read/public-access helpers for the country auto-population feature; the concrete
router wiring lives under ``routers``.
"""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

__all__: list[str] = []
