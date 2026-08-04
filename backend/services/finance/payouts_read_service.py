"""Service methods for payout read operations."""
from sqlalchemy.orm import Session
from data.models import Payout


def get_all_payouts(db: Session, skip: int = 0, limit: int = 20) -> list[Payout]:
    """Get all payouts with pagination."""
    return (
        db.query(Payout)
        .order_by(Payout.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_payout_by_id(db: Session, payout_id: int) -> Payout | None:
    """Get a payout by ID."""
    return db.query(Payout).filter(Payout.id == payout_id).first()


def get_payouts_by_supplier(db: Session, supplier_id: int) -> list[Payout]:
    """Get all payouts for a supplier."""
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier_id)
        .order_by(Payout.created_at.desc())
        .all()
    )


def get_payout_summary(db: Session) -> dict:
    """Get payout summary statistics."""
    from sqlalchemy import func as sqlfunc
    pending = (
        db.query(sqlfunc.sum(Payout.amount))
        .filter(Payout.status == "pending")
        .scalar()
        or 0
    )
    completed = (
        db.query(sqlfunc.sum(Payout.amount))
        .filter(Payout.status == "completed")
        .scalar()
        or 0
    )
    total = db.query(sqlfunc.count(Payout.id)).scalar() or 0
    return {
        "pending_total": float(pending),
        "completed_total": float(completed),
        "total_count": total,
    }
