"""Admin Export Router — CSV exports for reporting (pay-equity, etc.)."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from data.db import get_db
from services.core.internal_router_service import compute_pay_equity_rows

router = APIRouter()


@router.get("/pay-equity")
def export_pay_equity(db: Session = Depends(get_db)):
    """Export pay-equity metrics as a CSV file."""
    import csv
    metrics = compute_pay_equity_rows(db)
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

