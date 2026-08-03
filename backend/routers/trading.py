from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from data.db import get_db
from data.controllers_admin_controller import require_admin
from services import trading_service as trading
from services.core.internal_router_service import (
    get_purchase_order,
    get_goods_receipt_note,
    get_sales_order,
    get_stock_movements as get_stock_movements_from_db,
)

router = APIRouter()


# â”€â”€ Schemas â”€â”€


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
    currency: str = "OMR"
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
    currency: str = "OMR"
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


# â”€â”€ Purchase Orders â”€â”€


@router.post("/purchase-orders", summary="Create a purchase order")
def create_po(payload: POInput, db: Session = Depends(get_db),
              _admin: dict = Depends(require_admin)):
    try:
        po = trading.create_purchase_order(
            db, supplier_id=payload.supplier_id,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            warehouse_id=payload.warehouse_id,
            currency=payload.currency,
            notes=payload.notes, terms=payload.terms,
            shipping_address=payload.shipping_address,
            country_code=payload.country_code,
            lines=[l.model_dump() for l in payload.lines],
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return po


@router.get("/purchase-orders", summary="List purchase orders")
def list_pos(status: str = None, supplier_id: int = None,
             country_code: str = None, limit: int = 50, offset: int = 0,
             db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_purchase_orders(db, status=status, supplier_id=supplier_id,
                                         country_code=country_code, limit=limit, offset=offset)


@router.get("/purchase-orders/{po_id}", summary="Get a purchase order")
def get_po(po_id: int, db: Session = Depends(get_db),
           _admin: dict = Depends(require_admin)):
    return get_purchase_order(db, po_id=po_id)


@router.post("/purchase-orders/{po_id}/confirm", summary="Confirm a purchase order")
def confirm_po(po_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        po = trading.confirm_purchase_order(db, po_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return po


@router.post("/purchase-orders/{po_id}/receive", summary="Receive goods against a PO")
def receive_po(po_id: int, payload: GRNCreate, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        grn = trading.receive_purchase_order(db, po_id, payload.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))
    return grn


# â”€â”€ Goods Receipt Notes â”€â”€


@router.get("/goods-receipts", summary="List goods receipt notes")
def list_grns(po_id: int = None, status: str = None,
              country_code: str = None, limit: int = 50, offset: int = 0,
              db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_goods_receipts(db, po_id=po_id, status=status,
                                        country_code=country_code, limit=limit, offset=offset)


@router.get("/goods-receipts/{grn_id}", summary="Get a goods receipt note")
def get_grn(grn_id: int, db: Session = Depends(get_db),
            _admin: dict = Depends(require_admin)):
    return get_goods_receipt_note(db, grn_id=grn_id)


# â”€â”€ 3-Way Match â”€â”€


@router.post("/three-way-match", summary="Run 3-way match (PO vs GRN vs Bill)")
def three_way_match(payload: ThreeWayMatchInput, db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    try:
        result = trading.three_way_match(
            db, po_id=payload.po_id, grn_id=payload.grn_id, bill_id=payload.bill_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result


# â”€â”€ Sales Orders â”€â”€


@router.post("/sales-orders", summary="Create a sales order")
def create_so(payload: SOInput, db: Session = Depends(get_db),
              _admin: dict = Depends(require_admin)):
    try:
        so = trading.create_sales_order(
            db, customer_id=payload.customer_id,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            warehouse_id=payload.warehouse_id,
            currency=payload.currency,
            customer_po_number=payload.customer_po_number,
            shipping_address=payload.shipping_address,
            billing_address=payload.billing_address,
            notes=payload.notes, terms=payload.terms,
            country_code=payload.country_code,
            lines=[l.model_dump() for l in payload.lines],
            created_by=_admin.get("id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so


@router.get("/sales-orders", summary="List sales orders")
def list_sos(status: str = None, customer_id: int = None,
             country_code: str = None, limit: int = 50, offset: int = 0,
             db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    return trading.list_sales_orders(db, status=status, customer_id=customer_id,
                                      country_code=country_code, limit=limit, offset=offset)


@router.get("/sales-orders/{so_id}", summary="Get a sales order")
def get_so(so_id: int, db: Session = Depends(get_db),
           _admin: dict = Depends(require_admin)):
    return get_sales_order(db, so_id=so_id)


@router.post("/sales-orders/{so_id}/confirm", summary="Confirm a sales order")
def confirm_so(so_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        so = trading.confirm_sales_order(db, so_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so


@router.post("/sales-orders/{so_id}/invoice", summary="Generate AR invoice from sales order")
def invoice_so(so_id: int, db: Session = Depends(get_db),
               _admin: dict = Depends(require_admin)):
    try:
        inv = trading.invoice_sales_order(db, so_id, created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return inv


@router.post("/sales-orders/{so_id}/dispatch", summary="Dispatch goods & post COGS")
def dispatch_so(so_id: int, payload: DispatchInput = DispatchInput(),
                db: Session = Depends(get_db),
                _admin: dict = Depends(require_admin)):
    try:
        so = trading.dispatch_sales_order(db, so_id, payload.model_dump(),
                                           created_by=_admin.get("id"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return so


# â”€â”€ Warehouses â”€â”€


@router.post("/warehouses", summary="Create a warehouse")
def create_warehouse(payload: WarehouseInput, db: Session = Depends(get_db),
                     _admin: dict = Depends(require_admin)):
    try:
        wh = trading.create_warehouse(
            db, name=payload.name, code=payload.code,
            address=payload.address, city=payload.city,
            country_code=payload.country_code,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return wh


@router.get("/warehouses", summary="List warehouses")
def list_warehouses(country_code: str = None,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return trading.list_warehouses(db, country_code=country_code)


# â”€â”€ Stock â”€â”€


@router.get("/stock", summary="Get stock levels")
def stock_levels(product_id: int = None, warehouse_id: int = None,
                 db: Session = Depends(get_db),
                 _admin: dict = Depends(require_admin)):
    return trading.get_stock_level(db, product_id=product_id, warehouse_id=warehouse_id)


@router.get("/stock/movements", summary="List stock movements")
def stock_movements(product_id: int = None, limit: int = 100, offset: int = 0,
                    db: Session = Depends(get_db),
                    _admin: dict = Depends(require_admin)):
    return get_stock_movements_from_db(db, product_id=product_id, warehouse_id=None, limit=limit, offset=offset)


# â”€â”€ Dunning â”€â”€


@router.post("/dunning/run", summary="Run dunning engine")
def run_dunning(as_of: date = None, db: Session = Depends(get_db),
                _admin: dict = Depends(require_admin)):
    return trading.run_dunning_engine(db, as_of=as_of)