"""Admin email campaign router."""
from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from domains.comms.services.marketing.campaign_geography_service import create_campaign
from domains.comms.services.marketing.campaign_geography_service import delete_campaign
from domains.comms.services.marketing.campaign_geography_service import email_metrics
from domains.comms.services.marketing.campaign_geography_service import list_all_campaigns
from domains.comms.services.marketing.campaign_geography_service import list_campaigns

router = APIRouter(prefix="/api/v1/admin")


@router.get("/campaigns", response_model=list[EmailCampaignOut])
def list_all_campaigns_route(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all email campaigns across all countries (consolidated view)."""
    return list_all_campaigns(db)


@router.get("/metrics")
def admin_email_metrics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Consolidated email metrics across all countries."""
    return email_metrics(db)


@router.get("/campaigns/{country_code}")
def list_campaigns_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_campaigns(db, country_code, page, page_size)
    finally:
        clear_rls_context()


@router.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)
def create_campaign_route(country_code: str = Path(..., description="ISO country code"), payload: EmailCampaignCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_campaign(db, payload, country_code)
    finally:
        clear_rls_context()


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign_route(country_code: str = Path(..., description="ISO country code"), campaign_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_campaign(db, campaign_id, country_code)
    finally:
        clear_rls_context()
