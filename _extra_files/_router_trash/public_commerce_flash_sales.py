"""Flash sales router.

Thin orchestration layer: DB writes are delegated to
``controllers.flash_sales_controller`` (W1 — routers must not write to the DB).
The endpoints, paths and response shapes are unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from data.schemas import FlashSaleCreate
from data.models import FlashSale, User
from utils.datetime_utils import utcnow
from utils.dependencies import require_admin
from services.db_read import all_rows, first
from controllers.flash_sales_controller import (
    create_flash_sale as _create_flash_sale,
)
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("", response_model=dict)
def list_flash_sales(active_only: bool = True, db: Session = Depends(get_db)):
    filters = []
    if active_only:
        now = utcnow()
        filters = [FlashSale.is_active == True, FlashSale.starts_at <= now, FlashSale.ends_at >= now]  # noqa: E712
    return all_rows(db, FlashSale, filters)


@router.get("/{sale_id}", response_model=dict)
def get_flash_sale(sale_id: int, db: Session = Depends(get_db)):
    s = first(db, FlashSale, [FlashSale.id == sale_id])
    if not s: raise HTTPException(404)
    return s


@router.post("", response_model=dict)
def create_flash_sale(payload: FlashSaleCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    return _create_flash_sale(db=db, payload=payload)

