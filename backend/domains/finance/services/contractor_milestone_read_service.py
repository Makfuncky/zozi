"""Contractor milestone read service (owns the raw SQL read)."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_contractor_milestones(db: Session) -> list[dict]:
    """Return contractor payment/delivery milestones."""
    rows = db.execute(
        text("""
            SELECT m.id, m.employee_id, e.employee_code, m.milestone_type,
                   m.due_date, m.status
            FROM contractor_milestones m
            LEFT JOIN employees e ON e.id = m.employee_id
            ORDER BY m.due_date ASC
        """)
    ).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "milestone_type": r[3],
            "due_date": r[4],
            "status": r[5],
        }
        for r in rows
    ]
