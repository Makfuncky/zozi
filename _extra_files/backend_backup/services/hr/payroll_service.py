"""HR payroll read service.

Extracted from routers/payroll.py so the router no longer runs a query directly
against the session (CIR1). Payslip reads are simple ORM projections owned here.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from models import EmployeeDocument


def get_employee_payslips(employee_id: int, db: Session) -> Dict[str, Any]:
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
