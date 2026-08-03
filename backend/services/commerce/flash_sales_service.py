"""Flash sales router logic, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import List, Optional

from fastapi import HTTPException

from utils.datetime_utils import utcnow


def list_flash_sales(active_only: bool, skip: int, limit: int) -> List:
    from data.db import get_db_context
    from data.models import FlashSale

    with get_db_context() as db:
        q = db.query(FlashSale)
        if active_only:
            now = utcnow()
            q = q.filter(
                FlashSale.is_active == True,
                FlashSale.starts_at <= now,
                FlashSale.ends_at >= now,
            )
        return q.offset(skip).limit(limit).all()


def get_flash_sale(sale_id: int):
    from data.db import get_db_context
    from data.models import FlashSale

    with get_db_context() as db:
        s = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
        if not s:
            raise HTTPException(404)
        return s


def create_flash_sale(payload) -> object:
    from data.db import get_db_context
    from data.models import FlashSale, FlashSaleItem
    from data.services_write_helpers import add_and_flush, commit_only, flush_only, refresh_only

    with get_db_context() as db:
        items_data = payload.items
        sale = FlashSale(**payload.model_dump(exclude={"items"}))
        add_and_flush(db, sale)
        flush_only(db)
        for item in items_data:
            add_and_flush(db, FlashSaleItem(flash_sale_id=sale.id, **item.model_dump()))
        commit_only(db)
        refresh_only(db, sale)
        return sale
