"""Admin email campaign router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import CursorPage
from data.schemas import EmailCampaignCreate, EmailCampaignOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.pagination import cursor_paginate_desc
from services.communication.email_management_service import (
    EmailManagementService,
)


router = APIRouter()


def _get_email_svc(db: Session = Depends(get_db)) -> EmailManagementService:
    return EmailManagementService(db)


@router.get("/campaigns", response_model=list[EmailCampaignOut])
def list_all_campaigns(_: User = Depends(require_admin), svc: EmailManagementService = Depends(_get_email_svc)):
    """List all email campaigns across all countries (consolidated view)."""
    return svc.list_all_campaigns(limit=200)


@router.get("/metrics")
def admin_email_metrics(_: User = Depends(require_admin), svc: EmailManagementService = Depends(_get_email_svc)):
    """Consolidated email metrics across all countries."""
    return svc.get_email_metrics()


@router.get("/campaigns/{country_code}", response_model=CursorPage)
def list_campaigns(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    svc: EmailManagementService = Depends(_get_email_svc),
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = svc.get_campaigns_by_country_query(country_code)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)
def create_campaign(
    country_code: str = Path(..., description="ISO country code"),
    payload: EmailCampaignCreate = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
    svc: EmailManagementService = Depends(_get_email_svc),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return svc.create_campaign(payload.model_dump(), country_code.upper())
    finally:
        clear_rls_context()


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign(
    country_code: str = Path(..., description="ISO country code"),
    campaign_id: int = Path(...),
    _: User = Depends(require_admin),
    svc: EmailManagementService = Depends(_get_email_svc),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        try:
            campaign = svc.find_campaign_for_deletion(campaign_id, country_code)
        except ValueError:
            raise HTTPException(404)
        svc.delete_campaign(campaign)
        return {"message": "Deleted"}
    finally:
        clear_rls_context()
