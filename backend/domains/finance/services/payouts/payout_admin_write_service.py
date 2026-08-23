"""Admin payout write service.

Owns every DB mutation behind the country-scoped admin payout endpoints so the
router and controller layers stay write-free (W1 layer contract).

Each function takes ``db: Session`` first, performs the mutation, commits, and
raises ``HTTPException`` exactly as the original router code did.

NOTE: the ``audit_log(...)`` calls below are reproduced verbatim from the
original router endpoints (same arguments, same position *after* the commit) so
that runtime behaviour is byte-for-byte preserved by this refactor.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.payments import Payout
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)


def create_country_payout(
    db: Session,
    *,
    country_code: str,
    payload,
    admin_id,
    admin_username,
) -> Payout:
    """Create a payout for ``country_code`` and audit the action."""
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=country_code)
    db.add(p); db.commit(); db.refresh(p)
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=p.id,
        details={"amount": str(p.amount) if p.amount else None, "method": p.method},
    )
    return p


def verify_country_payout(
    db: Session,
    *,
    country_code: str,
    payout_id: int,
    payload,
    admin_id,
    admin_username,
) -> dict:
    """Mark a payout as verified (or the status supplied on the payload)."""
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code).first()
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
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"status": p.status, "reference": p.reference, "notes": p.notes},
    )
    return {"verified": True, "payout_id": payout_id}


def process_country_payout(
    db: Session,
    *,
    country_code: str,
    payout_id: int,
    admin_id,
    admin_username,
) -> dict:
    """Mark a payout as paid."""
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code).first()
    if not p:
        raise HTTPException(404)
    p.status = "paid"; p.processed_at = utcnow()
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"status": "paid"},
    )
    return {"message": "Payout processed"}
