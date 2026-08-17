"""Read helpers for purchase orders, goods receipt notes, sales orders and
stock movements.

Previously these ``db.query(...)`` lookups lived inline in
``routers/admin_supplier_trading.py`` and ``routers/trading.py``. They are
pure data-access functions (no commit, no HTTP concerns) so they belong in
the services layer. The routers delegate through
``controllers/admin/admin_supplier_trading_controller.py``.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models import GoodsReceiptNote, PurchaseOrder, SalesOrder, StockMovement


def get_purchase_order(db: Session, po_id: int) -> Optional[PurchaseOrder]:
    return db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()


def get_goods_receipt_note(db: Session, grn_id: int) -> Optional[GoodsReceiptNote]:
    return db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()


def get_sales_order(db: Session, so_id: int) -> Optional[SalesOrder]:
    return db.query(SalesOrder).filter(SalesOrder.id == so_id).first()


def list_stock_movements(
    db: Session,
    product_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    q = db.query(StockMovement)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    total = q.count()
    rows = q.order_by(StockMovement.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}
