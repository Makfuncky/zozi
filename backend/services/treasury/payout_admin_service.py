"""Payout admin service — DB operations for admin payout management."""
from typing import Optional

from sqlalchemy.orm import Session

from data.models import FinanceAutomationLog, Payout
from utils.audit_log import audit_log, AuditAction


def query_payouts_by_country(db: Session, country_code: str):
    return db.query(Payout).filter(Payout.country_code == country_code.upper())


def query_pending_payouts(db: Session):
    return db.query(Payout).filter(Payout.status == "pending")


def query_pending_payouts_by_country(db: Session, country_code: str):
    return db.query(Payout).filter(
        Payout.status == "pending",
        Payout.country_code == country_code.upper(),
    )


def get_payout(db: Session, payout_id: int, country_code: str) -> Optional[Payout]:
    return db.query(Payout).filter(
        Payout.id == payout_id,
        Payout.country_code == country_code.upper(),
    ).first()


def create_payout_record(db: Session, payload, country_code: str, current_admin) -> Payout:
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=country_code.upper())
    db.add(p)
    db.flush()
    db.commit()
    db.refresh(p)
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id, username=current_admin.username,
        user_role="admin", resource_type="payout",
        resource_id=p.id,
        details={"amount": str(p.amount) if p.amount else None, "method": p.method},
    )
    return p


def verify_payout_record(db: Session, p: Payout, status: str, note: Optional[str], bank_reference: Optional[str], current_admin) -> None:
    p.status = status
    from utils.datetime_utils import utcnow
    p.processed_at = utcnow()
    if note:
        p.notes = note
    if bank_reference:
        p.reference = bank_reference
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id, username=current_admin.username,
        user_role="admin", resource_type="payout",
        resource_id=p.id,
        details={"status": p.status, "reference": p.reference, "notes": p.notes},
    )


def process_payout_record(db: Session, p: Payout, current_admin) -> None:
    from utils.datetime_utils import utcnow
    p.status = "paid"
    p.processed_at = utcnow()
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id, username=current_admin.username,
        user_role="admin", resource_type="payout",
        resource_id=p.id,
        details={"status": "paid"},
    )


def query_recent_automation_logs(db: Session, kinds: list[str], limit: int = 20):
    return (
        db.query(FinanceAutomationLog)
        .filter(FinanceAutomationLog.kind.in_(kinds))
        .order_by(FinanceAutomationLog.created_at.desc())
        .limit(limit)
        .all()
    )
