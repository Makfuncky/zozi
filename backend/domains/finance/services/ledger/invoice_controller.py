"""Invoice controller broker.

The historical ``invoice_controller`` module (invoice create/read/update + HTML/PDF
rendering glue) was consolidated into the invoice service layer. This thin module
keeps the old import path alive (Law 3 sanctioned re-export) and provides the
stub entry points the employee finance router calls until the invoice domain is
fully wired.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session


def list_invoices(
    current_user: dict,
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    order_id: Optional[int] = None,
    *args,
    **kwargs,
) -> dict:
    """List invoices (stub)."""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "status": status,
        "order_id": order_id,
    }


def get_invoice_overview(db: Session, *args, **kwargs) -> dict:
    """Admin invoice overview (stub)."""
    return {"total": 0, "outstanding": 0, "recent": []}


def get_invoice(invoice_id: int, current_user: dict, db: Session, *args, **kwargs) -> dict:
    """Fetch a single invoice (stub)."""
    return {"id": invoice_id, "status": "not_found"}


def create_invoice_from_order(data: Any, current_user: dict, db: Session, *args, **kwargs) -> dict:
    """Create an invoice from an order (stub)."""
    return {"id": None, "status": "created"}


def update_invoice_status(invoice_id: int, data: Any, current_user: dict, db: Session, *args, **kwargs) -> dict:
    """Update invoice status (stub)."""
    return {"id": invoice_id, "status": "updated"}
