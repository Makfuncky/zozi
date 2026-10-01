"""Payroll service â€” calculation, batch processing, approval, and read operations.

Consolidates payroll_service.py (payroll calculation, batch processing, approval)
and payroll_read_service.py (payroll record reads, summary stats).
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.accounts.ports import get_current_user
from infrastructure.database.database import get_db
from domains.hr.models.employee_models import EmployeeDocument
from domains.hr.models.employee_models import PayrollRecord
from domains.hr.services.payroll.payroll_engine import PayrollEngine
from domains.hr.services.hr_permissions import check_permission

logger = logging.getLogger(__name__)

# Redis key prefix for pending payroll approvals
_PAYROLL_APPROVALS_PREFIX = "payroll:pending:"


def _get_redis():
    """Return Redis client or None."""
    try:
        from infrastructure.utils.redis_client import redis_client
        client = redis_client()
        if not client:
            return None
        try:
            if not client.ping():
                return None
        except Exception:
            return None
        return client
    except Exception:
        return None


def _get_pending_approvals() -> dict:
    """Get all pending payroll approvals from Redis."""
    redis = _get_redis()
    if not redis:
        return {}
    try:
        keys = redis.keys(f"{_PAYROLL_APPROVALS_PREFIX}*")
        result = {}
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            batch_key = key_str.replace(_PAYROLL_APPROVALS_PREFIX, "")
            data = redis.hgetall(key_str)
            if data:
                decoded = {}
                for k, v in data.items():
                    k_str = k.decode() if isinstance(k, bytes) else k
                    v_str = v.decode() if isinstance(v, bytes) else v
                    decoded[k_str] = v_str
                result[batch_key] = decoded
        return result
    except Exception:
        return {}


def _get_pending_approval(batch_key: str) -> dict | None:
    """Get a specific pending payroll approval from Redis."""
    redis = _get_redis()
    if not redis:
        return None
    try:
        data = redis.hgetall(f"{_PAYROLL_APPROVALS_PREFIX}{batch_key}")
        if not data:
            return None
        result = {}
        for k, v in data.items():
            k_str = k.decode() if isinstance(k, bytes) else k
            v_str = v.decode() if isinstance(v, bytes) else v
            result[k_str] = v_str
        return result
    except Exception:
        return None


def _set_pending_approval(batch_key: str, data: dict) -> None:
    """Store a pending payroll approval in Redis."""
    redis = _get_redis()
    if not redis:
        return
    try:
        key = f"{_PAYROLL_APPROVALS_PREFIX}{batch_key}"
        redis.hset(key, mapping=data)
    except Exception:
        pass


def _update_pending_approval(batch_key: str, field: str, value: str) -> None:
    """Update a field in a pending payroll approval."""
    redis = _get_redis()
    if not redis:
        return
    try:
        key = f"{_PAYROLL_APPROVALS_PREFIX}{batch_key}"
        redis.hset(key, field, value)
    except Exception:
        pass

class PayrollApproveBody(BaseModel):
    batch_id: str
    approved: bool = True
    notes: Optional[str] = None

def calculate_employee_payroll(employee_id: int, month: int, year: int, db: Session, current_user: dict):
    engine = PayrollEngine(db)
    period = date(year, month, 1)
    result = engine.calculate_monthly_payroll(employee_id, period)
    return result

def process_payroll_batch(country_code: str, month: int, year: int, db: Session, current_user: dict):
    """Generate payroll batch (Maker step)."""
    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.release", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.release permission")

    engine = PayrollEngine(db)
    period = date(year, month, 1)

    # Check if already approved
    batch_key = f"{country_code}:{year}:{month:02d}"
    existing = _get_pending_approval(batch_key)
    if existing and existing.get("status") == "disbursed":
        raise HTTPException(status_code=400, detail="This period has already been disbursed")

    payroll = engine.process_payroll_batch(period, country_code.upper())
    payroll["country_code"] = country_code.upper()
    payroll["status"] = "pending_approval"
    _set_pending_approval(batch_key, payroll)
    return payroll

def approve_payroll_batch(body: PayrollApproveBody, db: Session, current_user: dict):
    """Approve payroll for disbursement (Checker step - cannot be same user as Maker)."""
    parts = body.batch_id.split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid batch_id format")
    country_code = parts[1]
    year = parts[2]
    month = parts[3] if len(parts) > 3 else "01"
    batch_key = f"{country_code}:{year}:{month}"

    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.approve", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.approve permission")

    pending = _get_pending_approval(batch_key)
    if not pending or pending.get("status") != "pending_approval":
        raise HTTPException(status_code=400, detail="No pending payroll batch found for this period")

    maker_user_id = pending.get("maker_user_id")
    if maker_user_id and maker_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot approve your own payroll batch")

    if not body.approved:
        _update_pending_approval(batch_key, "status", "rejected")
        return {"status": "rejected", "batch_id": body.batch_id}

    # Execute auto-disbursement
    engine = PayrollEngine(db)
    period = date(int(year), int(month), 1)
    disbursement = engine.auto_disburse(period, approved_by=user_id)
    disbursement["batch_id"] = body.batch_id
    disbursement["status"] = "disbursed"
    disbursement["approved_by"] = user_id
    disbursement["approved_at"] = datetime.now(timezone.utc).isoformat()

    _set_pending_approval(batch_key, disbursement)
    return disbursement

def get_employee_payslips(employee_id: int, db: Session, current_user: dict):
    docs = (
        db.query(EmployeeDocument)
        .filter(
            EmployeeDocument.employee_id == employee_id,
            EmployeeDocument.doc_type == "payslip",
        )
        .order_by(EmployeeDocument.created_at.desc())
        .all()
    )
    return {
        "payslips": [
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "file_url": d.file_url,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    }

def employee_bank_accounts(employee_id: int, db: Session, current_user: dict):
    engine = PayrollEngine(db)
    return {"bank_accounts": engine.get_employee_bank_accounts(employee_id)}

def verify_bank_account(account_id: int, db: Session, current_user: dict):
    user_id = int(current_user.get("id", 0))
    engine = PayrollEngine(db)
    return engine.validate_bank_account(account_id, verified_by=user_id)

def payroll_status(country_code: str, db: Session):
    """Get current payroll batch status for a country."""
    results = {}
    pending_approvals = _get_pending_approvals()
    for key, value in pending_approvals.items():
        if key.startswith(country_code.upper()):
            results[key] = {
                "status": value.get("status"),
                "processed": value.get("processed"),
                "total_net": value.get("total_net"),
            }
    return {"payroll_batches": results}


# â”€â”€ Payroll Read Operations (merged from payroll_read_service.py) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


