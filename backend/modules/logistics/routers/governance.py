"""Logistics governance router — thin delegating to governance domain services."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logistics/governance", tags=["logistics", "governance"])


@router.get("/fraud-alerts")
def list_fraud_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.fraud.read")),
):
    """List fraud alerts for logistics partners."""
    from domains.governance.services.fraud_service import list_fraud_alerts
    return list_fraud_alerts(db, country_code=country_code, skip=(page - 1) * page_size, limit=page_size)


@router.get("/compliance-status")
def get_compliance_status(
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.compliance.read")),
):
    """Get compliance status for logistics."""
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
