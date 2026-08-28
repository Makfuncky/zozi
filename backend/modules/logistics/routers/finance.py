"""Logistics finance router — logistics-facing finance endpoints.

Provides logistics partners with access to their financial data including:
- Financial summaries
- Settlement history
- Transaction ledger
- COD remittance tracking
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac import get_current_user
from rbac.dependencies import require_feature
from domains.finance.services.finance_service import (
    logistics_financial_summary,
    logistics_list_settlements,
    logistics_list_ledger,
)
from domains.logistics.ports import get_logistics_partner_by_user_id


router = APIRouter(prefix="/api/v1/logistics/finance", tags=["logistics", "finance"])


# ══════════════════════════════════════════════════════════════════════════════
# LOGISTICS PARTNER FINANCIAL ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/summary", summary="Logistics partner financial summary")
def logistics_financial_summary_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("finance.treasury.read")),
):
    """Return financial summary for the authenticated logistics partner."""
    return logistics_financial_summary(db, current_user)


@router.get("/settlements", summary="Logistics partner settlements")
def logistics_list_settlements_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("finance.payout.read")),
):
    """Return settlement history for the authenticated logistics partner."""
    return logistics_list_settlements(skip, limit, status, db, current_user)


@router.get("/ledger", summary="Logistics partner transaction ledger")
def logistics_list_ledger_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("finance.ledger.read")),
):
    """Return transaction ledger for the authenticated logistics partner."""
    return logistics_list_ledger(skip, limit, db, current_user)


@router.get("/cod-remittances", summary="Logistics partner COD remittances")
def logistics_cod_remittances(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("finance.treasury.read")),
):
    """Return COD remittance records for the authenticated logistics partner."""
    partner = get_logistics_partner_by_user_id(db, int(current_user["id"]))
    if not partner:
        return []
    from domains.finance.services.treasury.cash_management_service import CashManagementService
    svc = CashManagementService(db)
    return svc.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner.id, status=status)


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/health", summary="Liveness probe for logistics finance router")
def health():
    return {"status": "ok", "router": "logistics/finance", "prefix": "/api/v1/logistics/finance"}
