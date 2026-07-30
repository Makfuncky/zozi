"""Admin email campaign router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, case as sql_case
from db.database import get_db
from models import EmailCampaign, NewsletterSubscriber, CampaignRecipient, User
from db.schemas import EmailCampaignCreate, EmailCampaignOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter()


@router.get("/campaigns", response_model=list[EmailCampaignOut])
def list_all_campaigns(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all email campaigns across all countries (consolidated view)."""
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(200).all()


@router.get("/metrics")
def admin_email_metrics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Consolidated email metrics across all countries."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
        sqlfunc.count(CampaignRecipient.id).label("total_sent"),
    ).first()
    total_sent = int(campaign_stats.total_sent or 0)
    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
    }


@router.get("/campaigns/{country_code}")
def list_campaigns(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(EmailCampaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)
def create_campaign(country_code: str = Path(..., description="ISO country code"), payload: EmailCampaignCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
        data = {k: v for k, v in payload.model_dump().items() if k in allowed and v is not None}
        data["country_code"] = country_code.upper()
        c = EmailCampaign(**data)
        db.add(c); db.commit(); db.refresh(c)
        return c
    finally:
        clear_rls_context()


@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign(country_code: str = Path(..., description="ISO country code"), campaign_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id, EmailCampaign.country_code == country_code.upper()).first()
        if not c: raise HTTPException(404)
        db.delete(c); db.commit()
        return {"message": "Deleted"}
    finally:
        clear_rls_context()

