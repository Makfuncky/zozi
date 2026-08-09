"""QR service (orders) — placeholder shim.

Imported for side-effects by the service registry. The operational QR generation
used by auth lives in ``services.triple_auth``; this module keeps the registry
import graph intact without pulling heavier dependencies into the load path.
"""
from __future__ import annotations

from typing import Any
import structlog
logger = structlog.get_logger(__name__)


class DynamicQRService:
    """Minimal QR token service used for side-effect imports."""

    def generate_token(self, *args: Any, **kwargs: Any) -> str:
        return ""


def generate_qr_token(*args: Any, **kwargs: Any) -> str:
    return ""


__all__ = ["DynamicQRService", "generate_qr_token"]
