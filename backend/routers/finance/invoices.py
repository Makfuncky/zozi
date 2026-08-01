"""
Invoices Router — supply chain invoice management.
All business logic in controllers/invoice_controller.py.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from db.database import get_db
from routers.auth import get_current_user
from utils.invoice_html import generate_invoice_html, generate_invoice_pdf_bytes
import controllers.invoice_controller as ctrl

router = APIRouter()


@router.get("/")
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    order_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List invoices — filtered by role (supplier sees own, admin sees all)."""
    return ctrl.list_invoices(current_user, db, page=page, page_size=page_size, status=status, order_id=order_id)


@router.get("/overview")
def invoice_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Admin overview — totals and recent invoices."""
    if current_user.get("role") not in ("admin", "sub_admin", "moderator"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return ctrl.get_invoice_overview(db)


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
def get_invoice_html(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Render invoice as printable HTML (browser print-to-PDF)."""
    inv_data = ctrl.get_invoice(invoice_id, current_user, db)
    return HTMLResponse(content=generate_invoice_html(inv_data))


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Render invoice as downloadable PDF."""
    inv_data = ctrl.get_invoice(invoice_id, current_user, db)
    pdf_bytes = generate_invoice_pdf_bytes(inv_data)
    filename = f"{inv_data['invoice_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ctrl.get_invoice(invoice_id, current_user, db)


@router.post("/", status_code=201)
def create_invoice(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create an invoice from an existing order."""
    return ctrl.create_invoice_from_order(data, current_user, db)


@router.put("/{invoice_id}/status")
def update_status(
    invoice_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Advance invoice status through supply chain stages."""
    return ctrl.update_invoice_status(invoice_id, data, current_user, db)

