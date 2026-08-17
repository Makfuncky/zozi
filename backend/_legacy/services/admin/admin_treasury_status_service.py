"""Admin payouts router."""
from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from _legacy.models import FinanceAutomationLog, Payout, User
from db.schemas import PayoutCreate, PayoutOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.datetime_utils import utcnow
from utils.audit import audit_log, AuditAction
from services.treasury.auto_payout_scheduler import get_background_job_status as _get_bg_status, start_auto_payout_background_job as _start_bg_job, stop_auto_payout_background_job as _stop_bg_job, run_auto_payout_sweep as _run_supplier_sweep, run_auto_logistics_payout_sweep as _run_logistics_sweep

class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = 'verified'

def list_payouts(country_code: str=Path(..., description='ISO country code'), _: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def create_payout(country_code: str=Path(..., description='ISO country code'), payload: PayoutCreate=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        model_cols = {c.name for c in Payout.__table__.columns}
        data = {k: v for (k, v) in payload.model_dump().items() if k in model_cols}
        p = Payout(**data, country_code=country_code.upper())
        db.add(p)
        db.commit()
        db.refresh(p)
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=p.id, details={'amount': str(p.amount) if p.amount else None, 'method': p.method})
        return p
    finally:
        clear_rls_context()

def list_pending_payouts(current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List all pending payouts (RLS-scoped if context is set)."""
    q = db.query(Payout).filter(Payout.status == 'pending')
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}

def list_pending_payouts_by_country(country_code: str=Path(..., description='ISO country code'), current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List pending payouts for a specific country."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.status == 'pending', Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def verify_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), payload: PayoutVerifyRequest=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Verify a payout."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404, 'Payout not found')
        p.status = payload.status if payload and payload.status else 'verified'
        p.processed_at = utcnow()
        if payload:
            if payload.note:
                p.notes = payload.note
            if payload.bank_reference:
                p.reference = payload.bank_reference
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': p.status, 'reference': p.reference, 'notes': p.notes})
        return {'verified': True, 'payout_id': payout_id}
    finally:
        clear_rls_context()

def process_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.status = 'paid'
        p.processed_at = utcnow()
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': 'paid'})
        return {'message': 'Payout processed'}
    finally:
        clear_rls_context()

def get_background_job_status_endpoint(db: Session=Depends(get_db), current_admin: User=Depends(require_admin)):
    """Return the current state of the auto-payout background job:
    is_running, last_run_at, last_run_status, last_error, total counts,
    and recent FinanceAutomationLog entries.
    """
    status = _get_bg_status()
    history = db.query(FinanceAutomationLog).filter(FinanceAutomationLog.kind.in_(['auto_payout', 'auto_logistics_payout'])).order_by(FinanceAutomationLog.created_at.desc()).limit(20).all()
    return {'status': status, 'history': [{'id': h.id, 'kind': h.kind, 'records_processed': h.records_processed, 'records_changed': h.records_changed, 'detail': h.detail, 'created_at': h.created_at.isoformat() if h.created_at else None} for h in history]}
