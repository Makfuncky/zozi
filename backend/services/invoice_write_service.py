"""Invoice write service — DB write operations for invoices and invoice items."""

from sqlalchemy.orm import Session

from models import Invoice, InvoiceItem


def create_invoice_with_items(db: Session, invoice_data: dict, items: list) -> Invoice:
    inv = Invoice(**invoice_data)
    db.add(inv)
    db.flush()

    for item_data in items:
        db.add(InvoiceItem(invoice_id=inv.id, **item_data))

    db.commit()
    db.refresh(inv)
    return inv


def update_invoice(db: Session, invoice: Invoice, updates: dict) -> Invoice:
    for key, value in updates.items():
        setattr(invoice, key, value)
    db.commit()
    db.refresh(invoice)
    return invoice