"""Employee governance router — thin delegating to governance domain services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_employee
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/employee/governance", tags=["employee", "governance"])


@router.get("/compliance-status")
def get_compliance_status(
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.compliance.read")),
):
    """Get compliance status for employees."""
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


@router.get("/access-review")
def get_access_review(
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.access.read")),
):
    """Get access review status."""
    from domains.governance.services.approval_matrix_service import get_access_review
    return get_access_review(db)
