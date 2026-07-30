"""
Invoice Controller — supply chain invoice management.
Covers the full lifecycle: supplier → logistics → customer receipt.
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Invoice, InvoiceItem, Order, OrderItem, Product, Shipment, User
from controllers.audit_controller import AuditAction, audit_log

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731

ALLOWED_STATUSES = ("draft", "issued", "in_transit", "delivered", "cancelled")


def _generate_invoice_number() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    uid = str(uuid.uuid4()).split("-")[0].upper()
    return f"INV-{stamp}-{uid}"


def _serialize_invoice(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "order_id": inv.order_id,
        "supplier_id": inv.supplier_id,
        "shipment_id": inv.shipment_id,
        "status": inv.status,
        "invoice_type": inv.invoice_type,
        "subtotal": float(inv.subtotal or 0),
        "tax_amount": float(inv.tax_amount or 0),
        "shipping_amount": float(inv.shipping_amount or 0),
        "discount_amount": float(inv.discount_amount or 0),
        "total_amount": float(inv.total_amount or 0),
        "currency": inv.currency,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "due_at": inv.due_at.isoformat() if inv.due_at else None,
        "picked_at": inv.picked_at.isoformat() if inv.picked_at else None,
        "dispatched_at": inv.dispatched_at.isoformat() if inv.dispatched_at else None,
        "delivered_at": inv.delivered_at.isoformat() if inv.delivered_at else None,
        "notes": inv.notes,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "supplier_name": inv.supplier.username if inv.supplier else None,
        "items": [_serialize_item(i) for i in (inv.items or [])],
    }


def _serialize_item(item: InvoiceItem) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "description": item.description,
        "quantity": item.quantity,
        "unit_price": float(item.unit_price or 0),
        "discount_amount": float(item.discount_amount or 0),
        "tax_rate": item.tax_rate,
        "line_total": float(item.line_total or 0),
    }


# ── List ──────────────────────────────────────────────────────────────────────

def list_invoices(
    current_user: dict,
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    order_id: Optional[int] = None,
) -> dict:
    role = current_user.get("role")
    q = db.query(Invoice)

    if role == "supplier":
        q = q.filter(Invoice.supplier_id == current_user["id"])
    elif role not in ("admin", "sub_admin", "moderator", "support"):
        # Customer: only their orders
        q = q.join(Order).filter(Order.user_id == current_user["id"])

    if status:
        q = q.filter(Invoice.status == status)
    if order_id:
        q = q.filter(Invoice.order_id == order_id)

    total = q.count()
    items = q.order_by(desc(Invoice.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [_serialize_invoice(i) for i in items],
    }


def get_invoice(invoice_id: int, current_user: dict, db: Session) -> dict:
    inv = (
        db.query(Invoice)
        .options(selectinload(Invoice.supplier), selectinload(Invoice.items))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    role = current_user.get("role")
    uid = current_user["id"]
    if role == "supplier" and inv.supplier_id != uid:
        raise HTTPException(status_code=403, detail="Access denied")
    if role == "customer":
        order = db.query(Order).filter(Order.id == inv.order_id, Order.user_id == uid).first()
        if not order:
            raise HTTPException(status_code=403, detail="Access denied")

    return _serialize_invoice(inv)


# ── Create from order ─────────────────────────────────────────────────────────

def create_invoice_from_order(data: dict, current_user: dict, db: Session) -> dict:
    """Supplier or admin creates an invoice for an order."""
    role = current_user.get("role")
    if role not in ("supplier", "admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Supplier or admin access required")

    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = (
        db.query(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    supplier_id = current_user["id"] if role == "supplier" else data.get("supplier_id", current_user["id"])

    # Check no duplicate invoice for same order+supplier
    existing = db.query(Invoice).filter(
        Invoice.order_id == order_id,
        Invoice.supplier_id == supplier_id,
        Invoice.invoice_type == "sale",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invoice already exists for this order")

    # Build line items from order items belonging to this supplier
    supplier_items = [
        item for item in order.items
        if item.product and item.product.supplier_id == supplier_id
    ]
    if role == "admin" and not supplier_items:
        supplier_items = order.items  # Admin can create for full order

    if not supplier_items:
        raise HTTPException(status_code=404, detail="No items found for this supplier in the order")

    subtotal = sum(float(i.price) * i.quantity for i in supplier_items)
    tax_rate = 0.05  # 5% VAT
    tax_amount = round(subtotal * tax_rate, 2)
    shipping_amount = float(order.shipping_amount or 0)
    discount_amount = float(order.discount_amount or 0)
    total_amount = subtotal + tax_amount + shipping_amount - discount_amount

    inv = Invoice(
        invoice_number=_generate_invoice_number(),
        order_id=order_id,
        supplier_id=supplier_id,
        shipment_id=data.get("shipment_id"),
        status="issued",
        invoice_type="sale",
        subtotal=subtotal,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total_amount,
        currency=data.get("currency", "AED"),
        issued_at=_utcnow(),
        notes=data.get("notes"),
    )
    db.add(inv)
    db.flush()

    for item in supplier_items:
        line_total = float(item.price) * item.quantity
        db.add(InvoiceItem(
            invoice_id=inv.id,
            product_id=item.product_id,
            description=item.product.name if item.product else f"Product #{item.product_id}",
            quantity=item.quantity,
            unit_price=float(item.price),
            discount_amount=0,
            tax_rate=tax_rate * 100,
            line_total=line_total,
        ))

    db.commit()
    db.refresh(inv)
    audit_log(
        db=db,
        user_id=current_user["id"],
        username=current_user.get("username", ""),
        user_role=role,
        action=AuditAction.INVOICE_CREATED,
        resource_type="invoice",
        resource_id=str(inv.id),
        details={"invoice_number": inv.invoice_number, "order_id": order_id},
    )
    # Email the invoice to the customer — enqueued async, failure is non-blocking
    try:
        from services.transactional_email_service import enqueue_invoice_email
        enqueue_invoice_email(cast(int, inv.id))
    except Exception:
        logger.warning("Failed to enqueue invoice email for invoice %s", inv.id)
    return _serialize_invoice(inv)


# ── Update status ─────────────────────────────────────────────────────────────

def update_invoice_status(invoice_id: int, data: dict, current_user: dict, db: Session) -> dict:
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    role = current_user.get("role")
    if role == "supplier" and inv.supplier_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if role not in ("supplier", "admin", "sub_admin", "logistics_partner"):
        raise HTTPException(status_code=403, detail="Access denied")

    new_status = data.get("status")
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {ALLOWED_STATUSES}")

    prev_status = inv.status
    inv.status = new_status
    now = _utcnow()
    if new_status == "in_transit":
        if not inv.picked_at:
            inv.picked_at = data.get("picked_at") or now
        if not inv.dispatched_at:
            inv.dispatched_at = data.get("dispatched_at") or now
    if new_status == "delivered" and not inv.delivered_at:
        inv.delivered_at = data.get("delivered_at") or now
    if "notes" in data:
        inv.notes = data["notes"]
    if "shipment_id" in data:
        inv.shipment_id = data["shipment_id"]

    inv.updated_at = now
    db.commit()
    db.refresh(inv)
    audit_log(
        db=db,
        user_id=current_user["id"],
        username=current_user.get("username", ""),
        user_role=role,
        action=AuditAction.INVOICE_STATUS_UPDATED,
        resource_type="invoice",
        resource_id=str(inv.id),
        details={"invoice_number": inv.invoice_number, "prev_status": prev_status, "new_status": new_status},
    )
    # Email delivery confirmation to customer — enqueued async, failure is non-blocking
    if new_status == "delivered":
        try:
            from services.transactional_email_service import enqueue_invoice_email
            enqueue_invoice_email(cast(int, inv.id))
        except Exception:
            logger.warning("Failed to enqueue delivery confirmation email for invoice %s", inv.id)
    return _serialize_invoice(inv)


# ── Admin overview ─────────────────────────────────────────────────────────────

def get_invoice_overview(db: Session) -> dict:
    from sqlalchemy import func as sqlfunc
    total = db.query(Invoice).count()
    by_status = db.query(Invoice.status, sqlfunc.count(Invoice.id)).group_by(Invoice.status).all()
    total_value = db.query(sqlfunc.sum(Invoice.total_amount)).scalar() or 0
    recent = db.query(Invoice).order_by(desc(Invoice.created_at)).limit(10).all()
    return {
        "total_invoices": total,
        "total_value": float(total_value),
        "by_status": {s: c for s, c in by_status},
        "recent": [_serialize_invoice(i) for i in recent],
    }


