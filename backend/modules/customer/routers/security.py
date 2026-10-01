"""Customer security router — thin delegating to domain services."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from rbac.dependencies import require_feature
from domains.security.services.core.security_service import list_fraud_events

router = APIRouter(prefix="/api/v1/customer/security", tags=["customer", "security"])


@router.get("/events")
def list_security_events(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("security.events.read")),
):
    """List the authenticated customer's security and fraud events (paginated)."""
    return list_fraud_events(
        page=page,
        size=page_size,
        user_id=current_user.id,
        ip_address=None,
        min_score=0,
        _=None,
        db=db,
    )
