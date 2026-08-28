"""Customer governance router — thin delegating to governance domain services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/governance", tags=["customer", "governance"])


@router.get("/referral-config")
def get_referral_config(
    db: Session = Depends(get_db),
    _: None = Depends(require_feature("governance.referral.read")),
):
    """Get referral program configuration."""
    from domains.governance.services.referral_service import get_referral_config
    return get_referral_config(db)


@router.post("/data-export-request")
def request_data_export(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _: None = Depends(require_feature("governance.compliance.read")),
):
    """Request GDPR data export."""
    from domains.governance.services.compliance_service import request_data_export
    return request_data_export(db, current_user.id)


@router.get("/consent")
def get_consent(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    _: None = Depends(require_feature("governance.compliance.read")),
):
    """Get user consent status."""
    from domains.governance.services.compliance_service import get_consent_status
    return get_consent_status(db, current_user.id)
