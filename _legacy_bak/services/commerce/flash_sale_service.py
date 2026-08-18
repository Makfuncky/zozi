"""Flash sale write service.

Holds the DB write logic for flash-sale creation so the router stays a thin
orchestration layer (W1: routers/controllers must not write to the DB). This
replicates the prior inline logic in ``routers/flash_sales.py`` exactly.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from _legacy.models import FlashSale, FlashSaleItem
from db.schemas import FlashSaleCreate
import structlog
logger = structlog.get_logger(__name__)


def create_flash_sale(db: Session, payload: FlashSaleCreate) -> FlashSale:
    """Persist a new flash sale and its items; returns the created row."""
    items_data = payload.items
    sale = FlashSale(**payload.model_dump(exclude={"items"}))
    db.add(sale)
    db.flush()
    for item in items_data or []:
        db.add(FlashSaleItem(flash_sale_id=sale.id, **item.model_dump()))
    db.commit()
    db.refresh(sale)
    return sale
