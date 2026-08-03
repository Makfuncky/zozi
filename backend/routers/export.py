"""Admin Export Router — CSV exports for reporting (pay-equity, etc.)."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from data.db import get_db
from data.models_employee_models import Employee

router = APIRouter()


def _compute_equity_rows(db: Session):
    rows = (
        db.query(
            Employee.department,
            Employee.gender,
            func.avg(Employee.salary),
        ).filter(Employee.salary.isnot(None), Employee.department.isnot(None))
        .group_by(Employee.department, Employee.gender)
        .all()
    )
    by_dept = {}
    for dept, gender, avg_sal in rows:
        by_dept.setdefault(dept, {})[gender or "unknown"] = float(avg_sal or 0)
    metrics = []
    for dept, vals in by_dept.items():
        avg_male = vals.get("male", 0.0)
        avg_female = vals.get("female", 0.0)
        disparity = (avg_male - avg_female) / avg_male * 100 if (avg_male > 0 and avg_female > 0) else 0.0
        metrics.append({
            "category": dept,
            "avg_male": round(avg_male, 2),
            "avg_female": round(avg_female, 2),
            "disparity_percent": round(disparity, 2),
            "flagged": disparity > 10,
        })
    return metrics


@router.get("/pay-equity")
def export_pay_equity(db: Session = Depends(get_db)):
    """Export pay-equity metrics as a CSV file."""
    metrics = _compute_equity_rows(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["category", "avg_male", "avg_female", "disparity_percent", "flagged"])
    for m in metrics:
        writer.writerow([
            m["category"], m["avg_male"], m["avg_female"],
            m["disparity_percent"], m["flagged"],
        ])
    csv_data = buf.getvalue()
    headers = {
        "Content-Disposition": f"attachment; filename=pay-equity-{datetime.now(timezone.utc).date().isoformat()}.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)

