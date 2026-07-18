"""Admin payouts router."""
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from models import Payout, User
from db.schemas import PayoutCreate, PayoutOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.datetime_utils import utcnow
from controllers.audit_controller import audit_log, AuditAction

router = APIRouter()


class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = "verified"


@router.get("/payouts/{country_code}", response_model=list[PayoutOut])
def list_payouts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(Payout).filter(Payout.country_code == country_code.upper()).order_by(Payout.created_at.desc()).all()
    finally:
        clear_rls_context()


@router.post("/payouts/{country_code}", response_model=PayoutOut, status_code=201)
def create_payout(
    country_code: str = Path(..., description="ISO country code"),
    payload: PayoutCreate = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        model_cols = {c.name for c in Payout.__table__.columns}
        data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
        p = Payout(**data, country_code=country_code.upper())
        db.add(p); db.commit(); db.refresh(p)
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=p.id,
            details={"amount": str(p.amount) if p.amount else None, "method": p.method},
        )
        return p
    finally:
        clear_rls_context()


@router.get("/pending")
def list_pending_payouts(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all pending payouts (RLS-scoped if context is set)."""
    return db.query(Payout).filter(Payout.status == "pending").order_by(Payout.created_at.desc()).all()


@router.get("/payouts/{country_code}/pending")
def list_pending_payouts_by_country(
    country_code: str = Path(..., description="ISO country code"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List pending payouts for a specific country."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper()).order_by(Payout.created_at.desc()).all()
    finally:
        clear_rls_context()


@router.post("/payouts/{country_code}/{payout_id}/verify")
def verify_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    payload: PayoutVerifyRequest = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Verify a payout."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404, "Payout not found")
        p.status = payload.status if payload and payload.status else "verified"
        p.processed_at = utcnow()
        if payload:
            if payload.note:
                p.notes = payload.note
            if payload.bank_reference:
                p.reference = payload.bank_reference
        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"status": p.status, "reference": p.reference, "notes": p.notes},
        )
        return {"verified": True, "payout_id": payout_id}
    finally:
        clear_rls_context()


@router.put("/payouts/{country_code}/{payout_id}/process")
def process_payout(
    country_code: str = Path(..., description="ISO country code"),
    payout_id: int = Path(...),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p: raise HTTPException(404)
        p.status = "paid"; p.processed_at = utcnow()
        db.commit()
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"status": "paid"},
        )
        return {"message": "Payout processed"}
    finally:
        clear_rls_context()

