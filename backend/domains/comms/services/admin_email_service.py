"""Admin email management service."""
from __future__ import annotations

from sqlalchemy import case as sql_case
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from infrastructure.database.schemas import EmailCampaignCreate
from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import NewsletterSubscriber

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context


def list_all_campaigns(db: Session) -> list:
    """List all email campaigns across all countries (consolidated view)."""
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(200).all()


def admin_email_metrics(db: Session) -> dict:
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


def list_campaigns(country_code: str, page: int, page_size: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(EmailCampaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


def create_campaign(country_code: str, payload: EmailCampaignCreate, db: Session) -> EmailCampaign:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
        data = {k: v for k, v in payload.model_dump().items() if k in allowed and v is not None}
        data["country_code"] = country_code.upper()
        c = EmailCampaign(**data)
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    finally:
        clear_rls_context()


def delete_campaign(country_code: str, campaign_id: int, db: Session) -> dict:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id, EmailCampaign.country_code == country_code.upper()).first()
        if not c:
            raise ValueError("Campaign not found")
        db.delete(c)
        db.commit()
        return {"message": "Deleted"}
    finally:
        clear_rls_context()


