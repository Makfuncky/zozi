# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Flash sale write service.

Holds the DB write logic for flash-sale creation so the router stays a thin
orchestration layer (W1: routers/controllers must not write to the DB). This
replicates the prior inline logic in ``routers/flash_sales.py`` exactly.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.comms.ports import FlashSale
from domains.comms.ports import FlashSaleItem
from infrastructure.database.schemas import FlashSaleCreate
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
