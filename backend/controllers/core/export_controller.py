"""Auto-migrated controller for routers/export.py (thin route contract)."""
from __future__ import annotations

from core.route_contract import get
from sqlalchemy.orm import Session

from services.core.export_service import export_pay_equity as _svc_export_pay_equity


@get("/api/v1/export/pay-equity", deps=["db"])
def export_pay_equity(db: Session):
    return _svc_export_pay_equity(db=db)
