'Treasury payout status controller.\n\nHolds the read/write logic for admin payout records (list / create / verify /\nprocess). Previously inline in ``routers.admin_treasury_status`` (CG1: ``Payout``\ninstantiation in router, W1: ``db.add``/``db.commit`` in router, DBA32: OFFSET\npagination). Routers now set RLS context, authorize, and delegate here.\n\nLists use keyset (seek) pagination via an opaque ``cursor`` (``created_at`` +\n``id``) instead of ``OFFSET``.\n'
from __future__ import annotations
import base64
from domains.comms.services.utility.db_read import query as db_read_query
from domains.comms.services.utility.db_read import execute as db_read_execute
from datetime import datetime
from typing import Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from domains.finance.models.payments import Payout
from infrastructure.utils.audit import AuditAction, audit_log
from domains.comms.services.utility.write_helpers import commit_and_refresh
from domains.comms.services.utility.write_helpers import commit_only
from infrastructure.utils.datetime_utils import utcnow

def _encode_cursor(dt: datetime, id_: int) -> str:
    raw = f'{dt.isoformat()}|{id_}'
    return base64.urlsafe_b64encode(raw.encode()).decode()

def _decode_cursor(cursor: Optional[str]) -> Optional[Tuple[datetime, int]]:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        (iso, id_) = raw.split('|')
        return (datetime.fromisoformat(iso), int(id_))
    except Exception:
        return None

def list_payouts(country_code: str, db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.country_code == country_code.upper())
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def list_pending_payouts(db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.status == 'pending')
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def list_pending_payouts_by_country(country_code: str, db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.status == 'pending', Payout.country_code == country_code.upper())
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def create_payout(country_code: str, payload, current_admin, db: Session) -> Payout:
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for (k, v) in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=country_code.upper())
    p = commit_and_refresh(db, p)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=p.id, details={'amount': str(p.amount) if p.amount else None, 'method': p.method})
    return p

def verify_payout(country_code: str, payout_id: int, payload, current_admin, db: Session) -> dict:
    p = db_read_query(db, Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
    if not p:
        raise HTTPException(404, 'Payout not found')
    p.status = payload.status if payload and payload.status else 'verified'
    p.processed_at = utcnow()
    if payload:
        if payload.note:
            p.notes = payload.note
        if payload.bank_reference:
            p.reference = payload.bank_reference
    commit_only(db)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': p.status, 'reference': p.reference, 'notes': p.notes})
    return {'verified': True, 'payout_id': payout_id}

def process_payout(country_code: str, payout_id: int, current_admin, db: Session) -> dict:
    p = db_read_query(db, Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
    if not p:
        raise HTTPException(404)
    p.status = 'paid'
    p.processed_at = utcnow()
    commit_only(db)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': 'paid'})
    return {'message': 'Payout processed'}