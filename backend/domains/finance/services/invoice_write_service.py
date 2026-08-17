"""Invoice write operations (canonical module).

Implements the invoice domain write surface. Previously stubbed with
``_missing_symbol`` placeholders; now contains real DB-write logic.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from _legacy.models import Invoice, InvoiceItem
import structlog
logger = structlog.get_logger(__name__)


def _apply_changes(record, changes: dict) -> None:
    for key, value in changes.items():
        if value is not None:
            setattr(record, key, value)


def create_invoice_with_items(
    db: Session,
    invoice_data: dict | None = None,
    items: list[dict] | None = None,
    **fields,
) -> Invoice:
    """Create an invoice with line items.

    Tolerant of both call shapes:
      * ``create_invoice_with_items(db, invoice_data, items)``  (controller, positional)
      * ``create_invoice_with_items(db, order_id=..., items=..., ...)`` (keyword/legacy)
    """
    if isinstance(invoice_data, dict):
        data = dict(invoice_data)
        if items is not None:
            data.setdefault("items", items)
        data.update(fields)
    else:
        data = dict(fields)
        if items is not None:
            data.setdefault("items", items)

    items_list = data.pop("items", None) or []

    order_id = data.get("order_id")
    if order_id is None:
        raise ValueError("order_id is required to create an invoice")
    order_id = int(order_id)
    shipment_id = data.get("shipment_id")
    supplier_id = data.get("supplier_id")
    invoice_type = data.get("invoice_type", "sale")
    tax_amount = data.get("tax_amount")
    shipping_amount = data.get("shipping_amount")
    discount_amount = data.get("discount_amount")
    currency = data.get("currency", "USD")
    country_code = data.get("country_code")
    notes = data.get("notes")

    subtotal = Decimal("0")
    invoice_items = []
    for item in items_list:
        quantity = int(item.get("quantity", 1))
        unit_price = Decimal(str(item.get("unit_price", 0)))
        discount = Decimal(str(item.get("discount_amount") or 0))
        tax_rate = Decimal(str(item.get("tax_rate") or 0))
        line_total = (unit_price * quantity - discount) * (Decimal("1") + tax_rate / Decimal("100"))
        subtotal += line_total
        invoice_items.append(
            InvoiceItem(
                product_id=item.get("product_id"),
                description=item.get("description", ""),
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount,
                tax_rate=tax_rate,
                line_total=line_total,
                country_code=country_code,
            )
        )

    total = subtotal + Decimal(str(shipping_amount or 0)) - Decimal(str(discount_amount or 0)) + Decimal(str(tax_amount or 0))
    invoice = Invoice(
        order_id=order_id,
        shipment_id=shipment_id,
        supplier_id=supplier_id,
        invoice_type=invoice_type,
        subtotal=subtotal,
        tax_amount=tax_amount,
        shipping_amount=shipping_amount,
        discount_amount=discount_amount,
        total_amount=total,
        currency=currency,
        country_code=country_code,
        notes=notes,
        **{k: v for k, v in data.items() if k not in _RESERVED_INVOICE_KEYS},
    )
    db.add(invoice)
    db.flush()
    for item in invoice_items:
        item.invoice_id = invoice.id
        db.add(item)
    db.commit()
    db.refresh(invoice)
    return invoice


# Keys consumed explicitly by create_invoice_with_items so they are not
# double-applied as generic model fields.
_RESERVED_INVOICE_KEYS = frozenset(
    {
        "order_id",
        "shipment_id",
        "supplier_id",
        "invoice_type",
        "tax_amount",
        "shipping_amount",
        "discount_amount",
        "currency",
        "country_code",
        "notes",
        "items",
    }
)


def update_invoice(db: Session, invoice_id: int, **changes) -> Invoice:
    obj = db.get(Invoice, invoice_id)
    if obj is None:
        raise ValueError(f"Invoice {invoice_id} not found")
    _apply_changes(obj, changes)
    db.commit()
    db.refresh(obj)
    return obj
