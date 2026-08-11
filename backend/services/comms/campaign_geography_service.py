"""Country-scoped email campaign read/write operations.

Owns the DB reads/writes for ``admin_comms_geography`` so the router stays free
of ``db.query``/``db.add``/``db.commit``/``db.delete``.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import case as sql_case
from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from data.models import CampaignRecipient, EmailCampaign, NewsletterSubscriber
import structlog
logger = structlog.get_logger(__name__)


def list_all_campaigns(db: Session, limit: int = 200) -> list[EmailCampaign]:
    """List all email campaigns across all countries (consolidated view)."""
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(limit).all()


def email_metrics(db: Session) -> dict:
    """Consolidated email metrics across all countries."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0  # noqa: E712
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


def list_campaigns(db: Session, country_code: str, page: int, page_size: int) -> dict:
    q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(EmailCampaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def create_campaign(db: Session, payload, country_code: str) -> EmailCampaign:
    allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
    data = {k: v for k, v in payload.model_dump().items() if k in allowed and v is not None}
    data["country_code"] = country_code.upper()
    c = EmailCampaign(**data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def delete_campaign(db: Session, campaign_id: int, country_code: str) -> dict:
    c = (
        db.query(EmailCampaign)
        .filter(EmailCampaign.id == campaign_id, EmailCampaign.country_code == country_code.upper())
        .first()
    )
    if not c:
        raise HTTPException(404)
    db.delete(c)
    db.commit()
    return {"message": "Deleted"}
