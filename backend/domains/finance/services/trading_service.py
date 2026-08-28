"""Trading Service — encapsulates purchase order, sales order, and stock movement logic."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.logistics.models.erp import (
    GoodsReceiptNote,
    PurchaseOrder,
    SalesOrder,
    StockMovement,
    Warehouse,
)

logger = logging.getLogger(__name__)

PurchaseOrderModel = PurchaseOrder
GoodsReceiptNoteModel = GoodsReceiptNote
SalesOrderModel = SalesOrder
StockMovementModel = StockMovement
WarehouseModel = Warehouse


def create_purchase_order(
    db: Session,
    supplier_id: int,
    order_date: Optional[datetime] = None,
    expected_delivery_date: Optional[datetime] = None,
    warehouse_id: Optional[int] = None,
    currency: str = "OMR",
    notes: Optional[str] = None,
    terms: Optional[str] = None,
    shipping_address: Optional[str] = None,
    country_code: Optional[str] = None,
    lines: Optional[list] = None,
    created_by: Optional[int] = None,
) -> dict:
    from domains.logistics.models.erp import PurchaseOrderLine
    po_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{supplier_id}"
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier_id,
        order_date=order_date or datetime.now(timezone.utc),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id,
        currency=currency,
        notes=notes,
        terms=terms,
        shipping_address=shipping_address,
        country_code=country_code,
        created_by=created_by,
        status="draft",
    )
    db.add(po)
    db.flush()

    total = 0
    for line in (lines or []):
        line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))
        total += line_total
        pol = PurchaseOrderLine(
            po_id=po.id,
            product_id=line.get("product_id"),
            product_name=line.get("product_name"),
            sku=line.get("sku"),
            description=line.get("description"),
            quantity_ordered=line.get("quantity_ordered", 0),
            unit_price=line.get("unit_price", 0),
            discount_percent=line.get("discount_percent", 0),
            tax_rate=line.get("tax_rate", 0),
            line_total=line_total,
            weight=line.get("weight"),
            volume=line.get("volume"),
        )
        db.add(pol)

    po.subtotal = total
    po.grand_total = total
    po.total_amount = total
    db.commit()
    db.refresh(po)
    return {"id": po.id, "po_number": po.po_number, "status": po.status, "grand_total": float(po.grand_total)}


def list_purchase_orders(
    db: Session,
    status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    if supplier_id:
        q = q.filter(PurchaseOrder.supplier_id == supplier_id)
    if country_code:
        q = q.filter(PurchaseOrder.country_code == country_code)
    return q.order_by(PurchaseOrder.id.desc()).offset(offset).limit(limit).all()


def get_purchase_order(db: Session, po_id: int) -> Optional[PurchaseOrder]:
    return db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()


def confirm_purchase_order(db: Session, po_id: int) -> dict:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    po.status = "confirmed"
    db.commit()
    return {"id": po.id, "status": po.status}


def receive_purchase_order(db: Session, po_id: int, payload: dict) -> dict:
    from domains.logistics.models.erp import GoodsReceiptNote, GoodsReceiptLine
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    grn_number = f"GRN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{po_id}"
    grn = GoodsReceiptNote(
        grn_number=grn_number,
        po_id=po_id,
        supplier_id=po.supplier_id,
        receipt_date=payload.get("receipt_date") or datetime.now(timezone.utc),
        warehouse_id=payload.get("warehouse_id") or po.warehouse_id,
        notes=payload.get("notes"),
        received_by=payload.get("received_by"),
        status="confirmed",
    )
    db.add(grn)
    db.flush()

    for line in payload.get("lines", []):
        grl = GoodsReceiptLine(
            grn_id=grn.id,
            po_line_id=line.get("po_line_id"),
            quantity_received=line.get("quantity_received", 0),
            quantity_accepted=line.get("quantity_accepted") or line.get("quantity_received", 0),
            rejection_reason=line.get("rejection_reason"),
            lot_number=line.get("lot_number"),
            expiry_date=line.get("expiry_date"),
        )
        db.add(grl)

    po.status = "received"
    db.commit()
    return {"id": grn.id, "grn_number": grn.grn_number, "po_id": po_id, "status": grn.status}


def list_goods_receipts(
    db: Session,
    po_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = db.query(GoodsReceiptNote)
    if po_id:
        q = q.filter(GoodsReceiptNote.po_id == po_id)
    if status:
        q = q.filter(GoodsReceiptNote.status == status)
    if country_code:
        q = q.filter(GoodsReceiptNote.country_code == country_code)
    return q.order_by(GoodsReceiptNote.id.desc()).offset(offset).limit(limit).all()


def get_goods_receipt(db: Session, grn_id: int) -> Optional[GoodsReceiptNote]:
    return db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()


def three_way_match(db: Session, po_id: int, grn_id: Optional[int] = None, bill_id: Optional[int] = None) -> dict:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    grn = None
    if grn_id:
        grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    return {
        "po_id": po_id,
        "po_number": po.po_number,
        "grn_id": grn_id,
        "grn_number": grn.grn_number if grn else None,
        "bill_id": bill_id,
        "matched": grn is not None,
    }


def create_sales_order(
    db: Session,
    customer_id: int,
    order_date: Optional[datetime] = None,
    expected_delivery_date: Optional[datetime] = None,
    warehouse_id: Optional[int] = None,
    currency: str = "OMR",
    customer_po_number: Optional[str] = None,
    shipping_address: Optional[str] = None,
    billing_address: Optional[str] = None,
    notes: Optional[str] = None,
    terms: Optional[str] = None,
    country_code: Optional[str] = None,
    lines: Optional[list] = None,
    created_by: Optional[int] = None,
) -> dict:
    from domains.logistics.models.erp import SalesOrderLine
    so_number = f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{customer_id}"
    so = SalesOrder(
        so_number=so_number,
        customer_id=customer_id,
        order_date=order_date or datetime.now(timezone.utc),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id,
        currency=currency,
        customer_po_number=customer_po_number,
        shipping_address=shipping_address,
        billing_address=billing_address,
        notes=notes,
        terms=terms,
        country_code=country_code,
        created_by=created_by,
        status="draft",
    )
    db.add(so)
    db.flush()

    total = 0
    for line in (lines or []):
        line_total = float(line.get("quantity_ordered", 0)) * float(line.get("unit_price", 0))
        total += line_total
        sol = SalesOrderLine(
            so_id=so.id,
            product_id=line.get("product_id"),
            product_name=line.get("product_name"),
            sku=line.get("sku"),
            description=line.get("description"),
            quantity_ordered=line.get("quantity_ordered", 0),
            unit_price=line.get("unit_price", 0),
            discount_percent=line.get("discount_percent", 0),
            tax_rate=line.get("tax_rate", 0),
            line_total=line_total,
            weight=line.get("weight"),
            volume=line.get("volume"),
        )
        db.add(sol)

    so.subtotal = total
    so.grand_total = total
    db.commit()
    db.refresh(so)
    return {"id": so.id, "so_number": so.so_number, "status": so.status, "grand_total": float(so.grand_total)}


def list_sales_orders(
    db: Session,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    country_code: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = db.query(SalesOrder)
    if status:
        q = q.filter(SalesOrder.status == status)
    if customer_id:
        q = q.filter(SalesOrder.customer_id == customer_id)
    if country_code:
        q = q.filter(SalesOrder.country_code == country_code)
    return q.order_by(SalesOrder.id.desc()).offset(offset).limit(limit).all()


def get_sales_order(db: Session, so_id: int) -> Optional[SalesOrder]:
    return db.query(SalesOrder).filter(SalesOrder.id == so_id).first()


def confirm_sales_order(db: Session, so_id: int) -> dict:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    so.status = "confirmed"
    db.commit()
    return {"id": so.id, "status": so.status}


def invoice_sales_order(db: Session, so_id: int, created_by: Optional[int] = None) -> dict:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    so.status = "invoiced"
    db.commit()
    return {"id": so.id, "status": so.status, "so_number": so.so_number}


def dispatch_sales_order(db: Session, so_id: int, payload: dict, created_by: Optional[int] = None) -> dict:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    so.status = "dispatched"
    db.commit()
    return {"id": so.id, "status": so.status, "so_number": so.so_number}


def create_warehouse(
    db: Session,
    name: str,
    code: str,
    address: Optional[str] = None,
    city: Optional[str] = None,
    country_code: Optional[str] = None,
) -> dict:
    wh = Warehouse(name=name, code=code, address=address, city=city, country_code=country_code)
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return {"id": wh.id, "name": wh.name, "code": wh.code}


def list_warehouses(db: Session, country_code: Optional[str] = None) -> list:
    q = db.query(Warehouse)
    if country_code:
        q = q.filter(Warehouse.country_code == country_code)
    return q.order_by(Warehouse.id).all()


def get_stock_level(db: Session, product_id: Optional[int] = None, warehouse_id: Optional[int] = None) -> list:
    q = db.query(StockMovement)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    return q.order_by(StockMovement.id.desc()).limit(100).all()


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


def run_dunning_engine(db: Session, as_of: Optional[datetime] = None) -> dict:
    return {"status": "completed", "as_of": str(as_of) if as_of else str(datetime.now(timezone.utc))}
