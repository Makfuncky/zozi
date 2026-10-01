"""Supplier governance router — thin delegating to governance domain services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from rbac.dependencies import require_feature

router = APIRouter(prefix="/supplier/governance", tags=["supplier", "governance"])


@router.get("/compliance-status")
def get_compliance_status(
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.compliance.read")),
):
    """Get compliance status for suppliers."""
    from domains.governance.services.compliance_service import get_compliance_status
    return get_compliance_status(db)


@router.get("/incidents")
def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.security.incident.read")),
):
    """List security incidents."""
    from domains.governance.services.incident.incident_service import list_incidents
    return list_incidents(db, country_code=country_code, skip=(page - 1) * page_size, limit=page_size)


@router.get("/disputes")
def list_disputes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.dispute.read")),
):
    """List supplier disputes."""
    from domains.governance.services.supplier_governance_service import list_disputes
    return list_disputes(db, skip=(page - 1) * page_size, limit=page_size)
