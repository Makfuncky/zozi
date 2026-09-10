"""Admin invoice service — operations for the ``/admin/invoices`` surface.

Thin wrapper that owns its own transaction (Law 2) and delegates reads
through the finance ports. Closes audit finding #5.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.finance.models.general_ledger import Invoice
from domains.finance.ports import get_invoice_by_id
# LAZY: from domains.finance.ports import get_invoice_by_id, list_invoices_page
from infrastructure.utils.pagination import MAX_PAGE_SIZE


def list_admin_invoices(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
) -> dict[str, Any]:
    """Paginated admin invoice list with optional filters.

    Wraps the keyset-paginated ``list_invoices_page`` from the finance
    ports layer and converts the cursor envelope into a simple page
    response that the admin UI understands.
    """
    cursor = None
    if page > 1:
        # offset-style page index into the cursor stream is intentionally
        # avoided — fall back to keyset on the first page only and let the
        # admin UI use the returned ``next_cursor`` for subsequent pages.
        cursor = None
    page_size = min(page_size, MAX_PAGE_SIZE)
    envelope = list_invoices_page(db, cursor=cursor, page_size=page_size)
    items: list[dict[str, Any]] = []
    for inv in envelope["items"]:
        if status and getattr(inv, "status", None) != status:
            continue
        if country_code and getattr(inv, "country_code", None) != country_code:
            continue
        items.append(_serialise(inv))
    return {
        "items": items,
        "total": len(items),
        "page": page,
        "page_size": page_size,
        "next_cursor": envelope.get("next_cursor"),
    }


def get_admin_invoice(db: Session, invoice_id: int) -> Optional[dict[str, Any]]:
    inv = get_invoice_by_id(db, invoice_id)
    return _serialise(inv) if inv else None


def issue_admin_invoice(
    db: Session,
    order_id: int,
    *,
    currency: str = "AED",
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Issue a new invoice for ``order_id``. Idempotent on existing pending invoice."""
    from domains.finance.models.general_ledger import Invoice

    existing = (
        db.query(Invoice)
        .filter(Invoice.order_id == order_id, Invoice.is_deleted == False)  # noqa: E712
        .order_by(Invoice.id.desc())
        .first()
    )
    if existing and existing.status == "pending":
        return _serialise(existing)
    inv = Invoice(
        order_id=order_id,
        currency=currency,
        status="pending",
        invoice_type="sale",
        notes=notes,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _serialise(inv)


def mark_invoice_paid(db: Session, invoice_id: int) -> dict[str, Any]:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return {"id": invoice_id, "status": "not_found"}
    from datetime import datetime, timezone

    inv.status = "paid"
    inv.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    return _serialise(inv)


def void_invoice(db: Session, invoice_id: int, reason: Optional[str] = None) -> dict[str, Any]:
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return {"id": invoice_id, "status": "not_found"}
    inv.status = "voided"
    if reason:
        inv.notes = (inv.notes or "") + f"\nVOID: {reason}"
    db.commit()
    db.refresh(inv)
    return _serialise(inv)


def invoice_pdf(db: Session, invoice_id: int) -> dict[str, Any]:
    """Return a structured payload the frontend can render or print.

    Full HTML/PDF rendering will be added in a follow-up; for now the
    endpoint returns the serialised invoice plus a ``render_url`` that
    points at a frontend route.
    """
    inv = get_invoice_by_id(db, invoice_id)
    if not inv:
        return {"id": invoice_id, "status": "not_found"}
    payload = _serialise(inv)
    payload["render_url"] = f"/admin/invoices/{invoice_id}/print"
    return payload


def _serialise(inv: Invoice) -> dict[str, Any]:
    return {
        "id": inv.id,
        "order_id": inv.order_id,
        "shipment_id": inv.shipment_id,
        "supplier_id": inv.supplier_id,
        "invoice_number": inv.invoice_number,
        "invoice_type": inv.invoice_type,
        "subtotal": str(inv.subtotal) if inv.subtotal is not None else None,
        "tax_amount": str(inv.tax_amount) if inv.tax_amount is not None else None,
        "shipping_amount": str(inv.shipping_amount) if inv.shipping_amount is not None else None,
        "discount_amount": str(inv.discount_amount) if inv.discount_amount is not None else None,
        "total_amount": str(inv.total_amount) if inv.total_amount is not None else None,
        "currency": inv.currency,
        "status": inv.status,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "due_at": inv.due_at.isoformat() if inv.due_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "notes": inv.notes,
        "country_code": inv.country_code,
    }