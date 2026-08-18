"""Treasury payout-admin service.

Thin service layer backing the payout-admin controller. Operations are kept
deliberately small; this module exists so the routers -> controllers ->
services circuit (CIR2) is preserved for payout administration.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.finance.models.finance import FinanceAutomationLog
from domains.payments.models.payments import Payout
import structlog
logger = structlog.get_logger(__name__)


def query_payouts_by_country(
    db: Session, country_code: str, skip: int = 0, limit: int = 20, **kwargs: Any
) -> list:
    return (
        db.query(Payout)
        .filter(Payout.country_code == country_code.upper())
        .order_by(Payout.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def query_pending_payouts(db: Session, skip: int = 0, limit: int = 20, **kwargs: Any) -> list:
    return (
        db.query(Payout)
        .filter(Payout.status == "pending")
        .order_by(Payout.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def query_pending_payouts_by_country(
    db: Session, country_code: str, skip: int = 0, limit: int = 20, **kwargs: Any
) -> list:
    return (
        db.query(Payout)
        .filter(Payout.country_code == country_code.upper(), Payout.status == "pending")
        .order_by(Payout.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_payout(db: Session, payout_id: int) -> Optional[Payout]:
    return db.query(Payout).filter(Payout.id == payout_id).first()


def create_payout_record(db: Session, **kwargs: Any) -> Payout:
    fields = {k: v for k, v in kwargs.items() if hasattr(Payout, k)}
    payout = Payout(**fields)
    db.add(payout)
    db.flush()
    db.commit()
    db.refresh(payout)
    return payout


def verify_payout_record(
    db: Session, payout_id: int, verified_by: Optional[int] = None, **kwargs: Any
) -> Optional[Payout]:
    payout = get_payout(db, payout_id)
    if payout is None:
        return None
    payout.status = "verified"
    db.commit()
    db.refresh(payout)
    return payout


def process_payout_record(
    db: Session, payout_id: int, processed_by: Optional[int] = None, **kwargs: Any
) -> Optional[Payout]:
    payout = get_payout(db, payout_id)
    if payout is None:
        return None
    payout.status = "processed"
    db.commit()
    db.refresh(payout)
    return payout


def query_recent_automation_logs(db: Session, limit: int = 20, **kwargs: Any) -> list:
    return db.query(FinanceAutomationLog).limit(limit).all()
