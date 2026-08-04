"""Service methods for Employee Self-Service (ESS) data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, Optional


def execute_ess_sql_scalar(db: Session, sql: str, params: dict) -> Optional[Any]:
    """Execute an ESS SQL query and return a single row mapping."""
    result = db.execute(text(sql), params)
    if hasattr(result, 'mappings'):
        return result.mappings().first()
    return result.fetchone()


def execute_ess_sql_rows(db: Session, sql: str, params: dict) -> list:
    """Execute an ESS SQL query and return all rows as mappings."""
    result = db.execute(text(sql), params)
    if hasattr(result, 'mappings'):
        return result.mappings().all()
    return result.fetchall()


def execute_ess_sql_scalar_value(db: Session, sql: str, params: dict) -> Any:
    """Execute an ESS SQL statement (e.g. INSERT ... RETURNING) and return a scalar value."""
    result = db.execute(text(sql), params)
    return result.scalar()


def create_leave_request(db: Session, employee_id: int, leave_type: str,
                         start_date: str, end_date: str, reason: str) -> int:
    """Insert a leave request and return the new leave request ID."""
    result = db.execute(text("""
        INSERT INTO leave_requests
            (employee_id, leave_type, start_date, end_date, reason, status, created_at)
        VALUES
            (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
        RETURNING id
    """), {
        "eid": employee_id,
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "now": text("NOW()"),
    })
    leave_id = result.scalar()
    db.commit()
    return leave_id
