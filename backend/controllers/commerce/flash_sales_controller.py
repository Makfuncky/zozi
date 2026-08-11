"""Flash sale controller.

Thin orchestration between the API layer and the flash-sale service. Satisfies
the CIR2 circuit rule (routers must call controllers, not services directly);
the DB write lives in ``services.commerce.flash_sale_service``.
"""
from __future__ import annotations

from data.models import FlashSale
from data.schemas import FlashSaleCreate
from services.commerce.flash_sale_service import (
    create_flash_sale as _create_flash_sale,
)
import structlog
logger = structlog.get_logger(__name__)


def create_flash_sale(db, payload: FlashSaleCreate) -> FlashSale:
    """Create a flash sale (delegates to the service)."""
    return _create_flash_sale(db=db, payload=payload)
