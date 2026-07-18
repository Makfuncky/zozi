"""Flash sales router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import FlashSale, FlashSaleItem, User
from db.schemas import FlashSaleCreate, FlashSaleOut
from utils.dependencies import require_admin
from utils.datetime_utils import utcnow

router = APIRouter()


@router.get("")
def list_flash_sales(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(FlashSale)
    if active_only:
        now = utcnow()
        q = q.filter(FlashSale.is_active == True, FlashSale.starts_at <= now, FlashSale.ends_at >= now)
    return q.all()


@router.get("/{sale_id}")
def get_flash_sale(sale_id: int, db: Session = Depends(get_db)):
    s = db.query(FlashSale).filter(FlashSale.id == sale_id).first()
    if not s: raise HTTPException(404)
    return s


@router.post("")
def create_flash_sale(payload: FlashSaleCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    items_data = payload.items
    sale = FlashSale(**payload.model_dump(exclude={"items"}))
    db.add(sale); db.flush()
    for item in items_data:
        db.add(FlashSaleItem(flash_sale_id=sale.id, **item.model_dump()))
    db.commit(); db.refresh(sale)
    return sale

