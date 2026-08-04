"""Service methods for payroll read operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import PayrollRecord


def get_payroll_records(
    db: Session, country_code: str, skip: int = 0, limit: int = 20
) -> list[PayrollRecord]:
    """Get payroll records for a country with pagination."""
    return (
        db.query(PayrollRecord)
        .filter(PayrollRecord.country_code == country_code)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_payroll_record_by_id(db: Session, record_id: int) -> PayrollRecord | None:
    """Get a payroll record by ID."""
    return db.query(PayrollRecord).filter(PayrollRecord.id == record_id).first()


def get_payroll_summary(db: Session, country_code: str) -> dict:
    """Get payroll summary stats for a country."""
    from sqlalchemy import func as sqlfunc
    total = db.query(sqlfunc.sum(PayrollRecord.net_pay)).filter(
        PayrollRecord.country_code == country_code
    ).scalar() or 0
    count = (
        db.query(sqlfunc.count(PayrollRecord.id))
        .filter(PayrollRecord.country_code == country_code)
        .scalar()
        or 0
    )
    paid = (
        db.query(sqlfunc.count(PayrollRecord.id))
        .filter(PayrollRecord.country_code == country_code, PayrollRecord.status == "paid")
        .scalar()
        or 0
    )
    return {"total_paid": float(total), "total_records": count, "paid_count": paid}
