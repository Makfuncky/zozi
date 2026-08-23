from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
from domains.finance.services.finance import trading_service as trading

class POLineInput(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity_ordered: float
    unit_price: float
    discount_percent: float = 0
    tax_rate: float = 0
    weight: Optional[float] = None
    volume: Optional[float] = None

class POLineOut(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: Optional[str]
    sku: Optional[str]
    quantity_ordered: float
    unit_price: float
    line_total: float

class POOut(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    supplier_name: Optional[str]
    status: str
    grand_total: float
    currency: str
    created_at: datetime

class GRNLineInput(BaseModel):
    po_line_id: int
    quantity_received: float
    quantity_accepted: Optional[float] = None
    rejection_reason: Optional[str] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None

class GRNCreate(BaseModel):
    receipt_date: Optional[datetime] = None
    warehouse_id: Optional[int] = None
    notes: Optional[str] = None
    received_by: Optional[int] = None
    lines: list[GRNLineInput]

class SOLineInput(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity_ordered: float
    unit_price: float
    discount_percent: float = 0
    tax_rate: float = 0
    weight: Optional[float] = None
    volume: Optional[float] = None

class POInput(BaseModel):
    supplier_id: int
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    warehouse_id: Optional[int] = None
    currency: str = 'OMR'
    notes: Optional[str] = None
    terms: Optional[str] = None
    shipping_address: Optional[str] = None
    country_code: Optional[str] = None
    lines: list[POLineInput]

class SOInput(BaseModel):
    customer_id: int
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    warehouse_id: Optional[int] = None
    currency: str = 'OMR'
    customer_po_number: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    country_code: Optional[str] = None
    lines: list[SOLineInput]

class ThreeWayMatchInput(BaseModel):
    po_id: int
    grn_id: Optional[int] = None
    bill_id: Optional[int] = None

class WarehouseInput(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None

class DispatchInput(BaseModel):
    dispatch_date: Optional[datetime] = None
    quantities: dict[str, float] = {}

def get_po(po_id: int, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    po = db.query(trading.PurchaseOrder).filter(trading.PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(404, 'Purchase order not found')
    return po

def get_grn(grn_id: int, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    grn = db.query(trading.GoodsReceiptNote).filter(trading.GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(404, 'Goods receipt note not found')
    return grn

def get_so(so_id: int, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    so = db.query(trading.SalesOrder).filter(trading.SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(404, 'Sales order not found')
    return so

def stock_movements(product_id: int=None, limit: int=100, offset: int=0, db: Session=Depends(get_db), _admin: dict=Depends(require_admin)):
    q = db.query(trading.StockMovement)
    if product_id:
        q = q.filter(trading.StockMovement.product_id == product_id)
    total = q.count()
    rows = q.order_by(trading.StockMovement.id.desc()).offset(offset).limit(limit).all()
    return {'total': total, 'items': rows}
