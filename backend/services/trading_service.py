from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from models import (
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceiptNote, GoodsReceiptLine,
    SalesOrder, SalesOrderLine,
    Warehouse, StockMovement,
    Vendor, Customer, Product, ProductVariant,
    APBill, ARInvoice, JournalEntry, Account, JournalEntryLine,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

INVENTORY_ACCOUNT = "1060"
COGS_ACCOUNT = "6000"
AP_ACCOUNT = "2010"
AR_ACCOUNT = "1035"
REVENUE_ACCOUNT = "4040"
VAT_OUTPUT_ACCOUNT = "2040"
VAT_INPUT_ACCOUNT = "2050"


def _next_number(db: Session, prefix: str, table_column) -> str:
    last = db.query(func.max(table_column)).filter(
        table_column.like(f"{prefix}-%")
    ).scalar()
    seq = 1
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    return f"{prefix}-{seq:05d}"


# ── Purchase Order ──


def create_purchase_order(
    db: Session, *, supplier_id: int, order_date: datetime = None,
    expected_delivery_date: datetime = None, warehouse_id: int = None,
    currency: str = "OMR", notes: str = None, terms: str = None,
    shipping_address: str = None, country_code: str = None,
    lines: list[dict] = None, created_by: int = None,
) -> PurchaseOrder:
    supplier = db.query(Vendor).filter(Vendor.id == supplier_id).first()
    if not supplier:
        raise ValueError("Supplier not found")
    po_number = _next_number(db, "PO", PurchaseOrder.po_number)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    po = PurchaseOrder(
        po_number=po_number, supplier_id=supplier_id,
        supplier_name=supplier.name,
        order_date=order_date or _utcnow(),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id, currency=currency,
        notes=notes, terms=terms, shipping_address=shipping_address,
        country_code=country_code, created_by=created_by,
        status="draft",
    )
    db.add(po)
    db.flush()
    po_lines = []
    for idx, ld in enumerate(lines or []):
        qty = Decimal(str(ld.get("quantity_ordered", 0)))
        price = Decimal(str(ld.get("unit_price", 0)))
        disc_pct = Decimal(str(ld.get("discount_percent", 0)))
        tax_rate = Decimal(str(ld.get("tax_rate", 0)))
        line_disc = qty * price * (disc_pct / Decimal("100"))
        line_sub = qty * price - line_disc
        line_tax = line_sub * (tax_rate / Decimal("100"))
        line_total = line_sub + line_tax
        subtotal += line_sub
        discount_total += line_disc
        tax_total += line_tax
        line = PurchaseOrderLine(
            po_id=po.id, product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            description=ld.get("description"),
            quantity_ordered=qty, unit_price=price,
            discount_percent=disc_pct, discount_amount=line_disc,
            tax_rate=tax_rate, tax_amount=line_tax,
            line_total=line_total,
            weight=ld.get("weight"), volume=ld.get("volume"),
            country_code=country_code,
        )
        db.add(line)
        po_lines.append(line)
    po.subtotal = subtotal
    po.discount_total = discount_total
    po.tax_total = tax_total
    po.grand_total = subtotal + tax_total
    db.commit()
    db.refresh(po)
    return po


def confirm_purchase_order(db: Session, po_id: int) -> PurchaseOrder:
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    if po.status != "draft":
        raise ValueError(f"Cannot confirm PO in status '{po.status}'")
    po.status = "confirmed"
    db.commit()
    db.refresh(po)
    return po


def receive_purchase_order(db: Session, po_id: int, grn_data: dict) -> GoodsReceiptNote:
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise ValueError("Purchase order not found")
    if po.status not in ("confirmed", "partially_received"):
        raise ValueError(f"Cannot receive PO in status '{po.status}'")
    supplier = db.query(Vendor).filter(Vendor.id == po.supplier_id).first()
    grn_number = _next_number(db, "GRN", GoodsReceiptNote.grn_number)
    grn = GoodsReceiptNote(
        grn_number=grn_number, po_id=po.id,
        supplier_id=po.supplier_id,
        receipt_date=grn_data.get("receipt_date") or _utcnow(),
        warehouse_id=grn_data.get("warehouse_id") or po.warehouse_id,
        status="confirmed", notes=grn_data.get("notes"),
        received_by=grn_data.get("received_by"),
        country_code=po.country_code,
    )
    db.add(grn)
    db.flush()
    line_map = {l.id: l for l in po.lines}
    total_received_qty = Decimal("0")
    total_accepted_qty = Decimal("0")
    for rl in (grn_data.get("lines") or []):
        po_line = line_map.get(rl.get("po_line_id"))
        if not po_line:
            continue
        qty_rec = Decimal(str(rl.get("quantity_received", 0)))
        qty_acc = Decimal(str(rl.get("quantity_accepted", qty_rec)))
        qty_rej = qty_rec - qty_acc
        cost = po_line.unit_price
        grn_line = GoodsReceiptLine(
            grn_id=grn.id, po_line_id=po_line.id,
            product_id=po_line.product_id,
            product_name=po_line.product_name,
            sku=po_line.sku,
            quantity_received=qty_rec,
            quantity_accepted=qty_acc,
            quantity_rejected=qty_rej,
            rejection_reason=rl.get("rejection_reason"),
            lot_number=rl.get("lot_number"),
            expiry_date=rl.get("expiry_date"),
            unit_cost=cost,
            country_code=po.country_code,
        )
        db.add(grn_line)
        po_line.quantity_received = (po_line.quantity_received or 0) + qty_acc
        total_received_qty += qty_rec
        total_accepted_qty += qty_acc
        _record_stock_movement(
            db, product_id=po_line.product_id,
            warehouse_id=grn.warehouse_id,
            movement_type="inbound",
            reference_type="grn", reference_id=grn.id,
            quantity_change=qty_acc,
            unit_cost=cost,
            country_code=po.country_code,
            created_by=grn_data.get("received_by"),
        )
    all_received = all(
        l.quantity_received >= l.quantity_ordered
        for l in po.lines if l.quantity_ordered > 0
    )
    po.status = "received" if all_received else "partially_received"
    po.delivery_date = grn.receipt_date
    po.warehouse_id = grn.warehouse_id or po.warehouse_id
    _post_grn_inventory_journal(db, grn, po)
    db.commit()
    db.refresh(grn)
    return grn


def _post_grn_inventory_journal(db: Session, grn: GoodsReceiptNote, po: PurchaseOrder) -> None:
    total_inventory = Decimal("0")
    for gl_ in grn.lines:
        cost = gl_.unit_cost or Decimal("0")
        total_inventory += cost * gl_.quantity_accepted
    if total_inventory <= 0:
        return
    lines = [
        JournalLineInput(
            account_code=INVENTORY_ACCOUNT, side="debit",
            amount=total_inventory,
            description=f"GRN {grn.grn_number} inventory receipt",
            entity_type="grn", entity_id=grn.id,
        ),
        JournalLineInput(
            account_code=AP_ACCOUNT, side="credit",
            amount=total_inventory,
            description=f"GRN {grn.grn_number} AP accrual",
            entity_type="grn", entity_id=grn.id,
        ),
    ]
    if po.country_code:
        setattr(lines[0], "country_code", po.country_code)
        setattr(lines[1], "country_code", po.country_code)
    try:
        gl.create_journal_entry(db, JournalEntryCreate(
            entry_date=grn.receipt_date,
            reference_type="grn", reference_id=grn.id,
            description=f"GRN {grn.grn_number} — inventory receipt & AP accrual",
            currency=po.currency, country_code=po.country_code,
            lines=lines,
        ))
    except Exception as e:
        logger.warning("GRN journal post failed (may retry): %s", e)


def three_way_match(
    db: Session, *, po_id: int = None, grn_id: int = None, bill_id: int = None,
) -> dict:
    results = {"po_ok": False, "grn_ok": False, "bill_ok": False, "match": False, "discrepancies": []}
    po = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.lines)
    ).filter(PurchaseOrder.id == po_id).first() if po_id else None
    grn = db.query(GoodsReceiptNote).options(
        joinedload(GoodsReceiptNote.lines)
    ).filter(GoodsReceiptNote.id == grn_id).first() if grn_id else None
    bill = db.query(APBill).filter(APBill.id == bill_id).first() if bill_id else None
    if po:
        results["po_ok"] = True
    if grn and po:
        po_total_qty = sum((l.quantity_ordered or 0) for l in po.lines)
        grn_total_qty = sum((l.quantity_accepted or 0) for l in grn.lines)
        if abs(grn_total_qty - po_total_qty) > Decimal("0.001"):
            results["discrepancies"].append(
                f"GRN qty ({grn_total_qty}) != PO qty ({po_total_qty})"
            )
        else:
            results["grn_ok"] = True
    if bill and po:
        if abs(bill.amount - po.grand_total) > Decimal("0.01"):
            results["discrepancies"].append(
                f"Bill amount ({bill.amount}) != PO total ({po.grand_total})"
            )
        elif abs(bill.tax_amount - po.tax_total) > Decimal("0.01"):
            results["discrepancies"].append(
                f"Bill tax ({bill.tax_amount}) != PO tax ({po.tax_total})"
            )
        else:
            results["bill_ok"] = True
    if grn is None and po:
        results["grn_ok"] = True
    if bill is None and po:
        results["bill_ok"] = True
    results["match"] = results["po_ok"] and results["grn_ok"] and results["bill_ok"]
    if results["match"] and bill and bill.status == "received":
        bill.status = "approved"
        db.commit()
    return results


# ── Sales Order ──


def create_sales_order(
    db: Session, *, customer_id: int, order_date: datetime = None,
    expected_delivery_date: datetime = None, warehouse_id: int = None,
    currency: str = "OMR", customer_po_number: str = None,
    shipping_address: str = None, billing_address: str = None,
    notes: str = None, terms: str = None, country_code: str = None,
    lines: list[dict] = None, created_by: int = None,
) -> SalesOrder:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise ValueError("Customer not found")
    if customer.credit_limit:
        current_ar = db.query(func.coalesce(func.sum(ARInvoice.amount), 0)).filter(
            ARInvoice.customer_id == customer_id,
            ARInvoice.status.in_(["issued", "partially_paid"]),
        ).scalar()
        new_total = sum(
            Decimal(str(l.get("unit_price", 0))) * Decimal(str(l.get("quantity_ordered", 0)))
            for l in (lines or [])
        )
        if (current_ar or 0) + new_total > customer.credit_limit:
            raise ValueError("Order would exceed customer credit limit")
    so_number = _next_number(db, "SO", SalesOrder.so_number)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    so = SalesOrder(
        so_number=so_number, customer_id=customer_id,
        customer_name=customer.name,
        customer_po_number=customer_po_number,
        order_date=order_date or _utcnow(),
        expected_delivery_date=expected_delivery_date,
        warehouse_id=warehouse_id, currency=currency,
        shipping_address=shipping_address,
        billing_address=billing_address,
        notes=notes, terms=terms,
        country_code=country_code, created_by=created_by,
        status="draft",
    )
    db.add(so)
    db.flush()
    for ld in (lines or []):
        qty = Decimal(str(ld.get("quantity_ordered", 0)))
        price = Decimal(str(ld.get("unit_price", 0)))
        disc_pct = Decimal(str(ld.get("discount_percent", 0)))
        tax_rate = Decimal(str(ld.get("tax_rate", 0)))
        line_disc = qty * price * (disc_pct / Decimal("100"))
        line_sub = qty * price - line_disc
        line_tax = line_sub * (tax_rate / Decimal("100"))
        line_total = line_sub + line_tax
        subtotal += line_sub
        discount_total += line_disc
        tax_total += line_tax
        line = SalesOrderLine(
            so_id=so.id, product_id=ld.get("product_id"),
            product_name=ld.get("product_name"), sku=ld.get("sku"),
            description=ld.get("description"),
            quantity_ordered=qty, unit_price=price,
            discount_percent=disc_pct, discount_amount=line_disc,
            tax_rate=tax_rate, tax_amount=line_tax,
            line_total=line_total,
            weight=ld.get("weight"), volume=ld.get("volume"),
            country_code=country_code,
        )
        db.add(line)
    so.subtotal = subtotal
    so.discount_total = discount_total
    so.tax_total = tax_total
    so.grand_total = subtotal + tax_total
    db.commit()
    db.refresh(so)
    return so


def confirm_sales_order(db: Session, so_id: int) -> SalesOrder:
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status != "draft":
        raise ValueError(f"Cannot confirm SO in status '{so.status}'")
    so.status = "confirmed"
    db.commit()
    db.refresh(so)
    return so


def invoice_sales_order(db: Session, so_id: int, invoice_date: datetime = None,
                        created_by: int = None) -> ARInvoice:
    so = db.query(SalesOrder).options(
        joinedload(SalesOrder.lines)
    ).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status not in ("confirmed", "invoiced", "partially_invoiced"):
        raise ValueError(f"Cannot invoice SO in status '{so.status}'")
    invoice_number = _next_number(db, "INV", ARInvoice.invoice_number)
    inv = ARInvoice(
        customer_id=so.customer_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date or _utcnow(),
        due_date=(invoice_date or _utcnow()) + timedelta(days=30),
        account_code=REVENUE_ACCOUNT,
        amount=so.grand_total,
        tax_amount=so.tax_total,
        description=f"Invoice for SO {so.so_number}",
        country_code=so.country_code,
        created_by=created_by,
        status="issued",
    )
    db.add(inv)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=inv.invoice_date,
        reference_type="so_invoice", reference_id=inv.id,
        description=f"AR invoice {invoice_number} for SO {so.so_number}",
        currency=so.currency, country_code=so.country_code,
        lines=[
            JournalLineInput(
                account_code=AR_ACCOUNT, side="debit",
                amount=so.grand_total,
                description=f"AR for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
            JournalLineInput(
                account_code=REVENUE_ACCOUNT, side="credit",
                amount=so.grand_total - so.tax_total,
                description=f"Revenue for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
            JournalLineInput(
                account_code=VAT_OUTPUT_ACCOUNT, side="credit",
                amount=so.tax_total,
                description=f"VAT for SO {so.so_number}",
                entity_type="ar_invoice", entity_id=inv.id,
            ),
        ],
    ), user_id=created_by)
    inv.linked_journal_entry_id = entry.id
    so.status = "invoiced"
    db.commit()
    db.refresh(inv)
    return inv


def dispatch_sales_order(db: Session, so_id: int, dispatch_data: dict,
                         created_by: int = None) -> SalesOrder:
    so = db.query(SalesOrder).options(
        joinedload(SalesOrder.lines)
    ).filter(SalesOrder.id == so_id).first()
    if not so:
        raise ValueError("Sales order not found")
    if so.status not in ("invoiced", "partially_dispatched"):
        raise ValueError(f"Cannot dispatch SO in status '{so.status}'")
    so.status = "dispatched"
    total_cogs = Decimal("0")
    for sol in so.lines:
        qty = dispatch_data.get("quantities", {}).get(str(sol.id))
        if qty:
            qty_disp = Decimal(str(qty))
            sol.quantity_dispatched = (sol.quantity_dispatched or 0) + qty_disp
            cost = _get_product_cost(db, sol.product_id)
            line_cogs = cost * qty_disp if cost else Decimal("0")
            total_cogs += line_cogs
            _record_stock_movement(
                db, product_id=sol.product_id,
                warehouse_id=so.warehouse_id,
                movement_type="outbound",
                reference_type="so", reference_id=so.id,
                quantity_change=-qty_disp,
                unit_cost=cost,
                country_code=so.country_code,
                created_by=created_by,
            )
    so.delivery_date = dispatch_data.get("dispatch_date") or _utcnow()
    if total_cogs > 0:
        try:
            gl.create_journal_entry(db, JournalEntryCreate(
                entry_date=so.delivery_date,
                reference_type="so_cogs", reference_id=so.id,
                description=f"COGS for SO {so.so_number}",
                currency=so.currency, country_code=so.country_code,
                lines=[
                    JournalLineInput(
                        account_code=COGS_ACCOUNT, side="debit",
                        amount=total_cogs,
                        description=f"COGS for SO {so.so_number}",
                        entity_type="sales_order", entity_id=so.id,
                    ),
                    JournalLineInput(
                        account_code=INVENTORY_ACCOUNT, side="credit",
                        amount=total_cogs,
                        description=f"Inventory reduction for SO {so.so_number}",
                        entity_type="sales_order", entity_id=so.id,
                    ),
                ],
            ), user_id=created_by)
        except Exception as e:
            logger.warning("COGS journal post failed for SO %s: %s", so.so_number, e)
    db.commit()
    db.refresh(so)
    return so


# ── Dunning Engine ──


def run_dunning_engine(db: Session, as_of: date = None) -> list[dict]:
    as_of = as_of or date.today()
    triggered = []
    invoices = db.query(ARInvoice).filter(
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date.isnot(None),
    ).all()
    for inv in invoices:
        days_overdue = (as_of - inv.due_date.date()).days if inv.due_date else 0
        reminders = []
        if days_overdue <= -7 and days_overdue > -14:
            reminders.append({"type": "reminder_1", "message": f"Payment due in {abs(days_overdue)} days for invoice {inv.invoice_number}"})
        elif days_overdue == 0:
            reminders.append({"type": "reminder_2", "message": f"Payment due today for invoice {inv.invoice_number}"})
        elif 1 <= days_overdue <= 7:
            reminders.append({"type": "reminder_3", "message": f"Invoice {inv.invoice_number} is {days_overdue} day(s) overdue — late fee may apply"})
        elif 8 <= days_overdue <= 30:
            reminders.append({"type": "reminder_4", "message": f"Invoice {inv.invoice_number} is {days_overdue} day(s) overdue — credit hold risk"})
        elif 31 <= days_overdue <= 60:
            reminders.append({"type": "escalation_1", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days — management alert"})
        elif 61 <= days_overdue <= 90:
            reminders.append({"type": "escalation_2", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days — legal warning"})
        elif days_overdue > 90:
            reminders.append({"type": "write_off_recommendation", "message": f"Invoice {inv.invoice_number} overdue {days_overdue} days — recommend write-off"})
        if reminders:
            triggered.append({
                "invoice_id": inv.id, "invoice_number": inv.invoice_number,
                "customer_id": inv.customer_id, "days_overdue": days_overdue,
                "amount": float(inv.amount), "reminders": reminders,
            })
            # Send dunning emails
            try:
                from services.transactional_email_service import enqueue_dunning_email
                for reminder in reminders:
                    enqueue_dunning_email(inv.id, reminder["type"], reminder["message"])
            except Exception as e:
                logger.warning("Failed to send dunning email for invoice %s: %s", inv.id, e)
    return triggered


# ── Stock ──


def _get_product_cost(db: Session, product_id: int) -> Optional[Decimal]:
    if not product_id:
        return None
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and product.cost_price:
        return Decimal(str(product.cost_price))
    return None


def _record_stock_movement(
    db: Session, *, product_id: int, warehouse_id: int = None,
    movement_type: str, reference_type: str = None, reference_id: int = None,
    quantity_change: Decimal, unit_cost: Decimal = None,
    country_code: str = None, created_by: int = None,
) -> StockMovement:
    if not product_id:
        return None
    last_mvt = db.query(StockMovement.quantity_after).filter(
        StockMovement.product_id == product_id,
        StockMovement.warehouse_id == warehouse_id,
    ).order_by(StockMovement.id.desc()).first()
    prev_qty = Decimal(str(last_mvt[0])) if last_mvt else Decimal("0")
    qty_after = prev_qty + quantity_change
    total_cost = (unit_cost or Decimal("0")) * abs(quantity_change) if quantity_change else Decimal("0")
    mvt = StockMovement(
        product_id=product_id, warehouse_id=warehouse_id,
        movement_type=movement_type,
        reference_type=reference_type, reference_id=reference_id,
        quantity_change=quantity_change, quantity_after=qty_after,
        unit_cost=unit_cost, total_cost=total_cost,
        country_code=country_code, created_by=created_by,
    )
    db.add(mvt)
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        new_stock = (product.stock or 0) + int(quantity_change)
        product.stock = max(0, new_stock)
    return mvt


def get_stock_level(db: Session, product_id: int = None, warehouse_id: int = None) -> list[dict]:
    q = db.query(
        StockMovement.product_id, Product.name, Product.sku,
        func.sum(StockMovement.quantity_change).label("current_stock"),
        func.max(StockMovement.created_at).label("last_movement"),
    ).join(Product, StockMovement.product_id == Product.id)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    q = q.group_by(StockMovement.product_id, Product.name, Product.sku)
    results = []
    for row in q.all():
        results.append({
            "product_id": row.product_id,
            "product_name": row.name,
            "sku": row.sku,
            "current_stock": float(row.current_stock or 0),
            "last_movement": row.last_movement.isoformat() if row.last_movement else None,
        })
    return results


# ── Warehouse ──


def create_warehouse(db: Session, *, name: str, code: str, address: str = None,
                     city: str = None, country_code: str = None) -> Warehouse:
    existing = db.query(Warehouse).filter(Warehouse.code == code).first()
    if existing:
        raise ValueError(f"Warehouse code '{code}' already exists")
    wh = Warehouse(name=name, code=code, address=address, city=city, country_code=country_code)
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


def list_warehouses(db: Session, country_code: str = None) -> list[Warehouse]:
    q = db.query(Warehouse)
    if country_code:
        q = q.filter(Warehouse.country_code == country_code)
    return q.order_by(Warehouse.name).all()


# ── PO / SO Listing ──


def list_purchase_orders(db: Session, status: str = None, supplier_id: int = None,
                          country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    if supplier_id:
        q = q.filter(PurchaseOrder.supplier_id == supplier_id)
    if country_code:
        q = q.filter(PurchaseOrder.country_code == country_code)
    total = q.count()
    rows = q.order_by(PurchaseOrder.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}


def list_sales_orders(db: Session, status: str = None, customer_id: int = None,
                       country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(SalesOrder)
    if status:
        q = q.filter(SalesOrder.status == status)
    if customer_id:
        q = q.filter(SalesOrder.customer_id == customer_id)
    if country_code:
        q = q.filter(SalesOrder.country_code == country_code)
    total = q.count()
    rows = q.order_by(SalesOrder.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}


def list_goods_receipts(db: Session, po_id: int = None, status: str = None,
                         country_code: str = None, limit: int = 50, offset: int = 0) -> dict:
    q = db.query(GoodsReceiptNote)
    if po_id:
        q = q.filter(GoodsReceiptNote.po_id == po_id)
    if status:
        q = q.filter(GoodsReceiptNote.status == status)
    if country_code:
        q = q.filter(GoodsReceiptNote.country_code == country_code)
    total = q.count()
    rows = q.order_by(GoodsReceiptNote.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}


# ── 3-Way Match Scanner ──


def scan_unmatched_pos(db: Session, country_code: str = None) -> dict:
    """
    Scan for purchase orders that haven't been fully matched (3-way match).
    Returns list of POs with GRN but no matching bill, or bill but no GRN.
    """
    results = {"scanned": 0, "unmatched": 0, "items": []}
    
    # Find POs with status 'received' (GRN confirmed) but no AP bill
    q = db.query(PurchaseOrder).filter(
        PurchaseOrder.status.in_(["received", "partial"]),
    )
    if country_code:
        q = q.filter(PurchaseOrder.country_code == country_code)
    
    pos = q.all()
    results["scanned"] = len(pos)
    
    for po in pos:
        # Check if AP bill exists for this PO
        has_bill = db.query(APBill).filter(
            APBill.linked_journal_entry_id.isnot(None),
            APBill.description.contains(f"PO-{po.po_number}"),
        ).first()
        
        if not has_bill:
            # Check if GRN exists
            has_grn = db.query(GoodsReceiptNote).filter(
                GoodsReceiptNote.po_id == po.id,
                GoodsReceiptNote.status == "confirmed",
            ).first()
            
            results["unmatched"] += 1
            results["items"].append({
                "po_id": po.id,
                "po_number": po.po_number,
                "status": po.status,
                "has_grn": bool(has_grn),
                "has_bill": False,
                "vendor_id": po.vendor_id,
                "total_amount": float(po.total_amount or 0),
            })
     
    return results


# ── E-commerce Auto-Invoice on Delivery (#11) ──────────


def auto_invoice_ecommerce_orders(db: Session, country_code: str = None) -> dict:
    """
    Auto-generate AR invoices for delivered e-commerce orders.
    Called daily by the automation scheduler.
    """
    from models import Order, ARInvoice, Account

    results = {"scanned": 0, "invoiced": 0, "skipped": 0, "errors": 0}

    orders = db.query(Order).filter(
        Order.payment_method == "card",
        Order.status == "delivered",
        Order.invoice_id.is_(None),
    )
    if country_code:
        orders = orders.filter(Order.country_code == country_code)

    results["scanned"] = orders.count()

    for order in orders.all():
        try:
            existing = db.query(ARInvoice).filter(
                ARInvoice.reference_order_id == order.id,
            ).first()
            if existing:
                results["skipped"] += 1
                continue

            invoice_number = _next_number(db, "INV", ARInvoice.invoice_number)
            now = _utcnow()

            revenue_acct = db.query(Account).filter(Account.code == "4010").first()
            vat_acct = db.query(Account).filter(Account.code == "2040").first()

            if not revenue_acct or not vat_acct:
                results["errors"] += 1
                continue

            lines = [
                JournalLineInput(
                    account_code="1100",
                    side="debit",
                    amount=order.total_amount,
                    description=f"AR for delivered order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                JournalLineInput(
                    account_code="4010",
                    side="credit",
                    amount=order.total_amount,
                    description=f"Sales revenue - Order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
                JournalLineInput(
                    account_code="2040",
                    side="credit",
                    amount=order.vat_amount or 0,
                    description=f"VAT output - Order #{order.id}",
                    entity_type="order",
                    entity_id=order.id,
                ),
            ]

            entry_data = JournalEntryCreate(
                entry_date=now,
                reference_type="ecommerce_invoice",
                reference_id=order.id,
                reference_number=invoice_number,
                description=f"Auto-invoice for delivered order #{order.id}",
                currency=order.currency or "OMR",
                country_code=country_code or order.country_code,
                lines=lines,
            )

            je = gl.create_journal_entry(db, entry_data)

            ar_invoice = ARInvoice(
                customer_id=order.user_id,
                invoice_number=invoice_number,
                invoice_date=now,
                due_date=now,
                account_code="1100",
                amount=order.total_amount,
                tax_amount=order.vat_amount,
                status="issued",
                linked_journal_entry_id=je.id,
                country_code=country_code or order.country_code,
                created_by=0,
            )
            db.add(ar_invoice)
            order.invoice_id = ar_invoice.id
            results["invoiced"] += 1
        except Exception as e:
            logger.warning("Auto-invoice failed for order %s: %s", order.id, e)
            results["errors"] += 1

    db.commit()
    return results