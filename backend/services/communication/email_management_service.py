"""Email management service — DB operations for templates, campaigns, suppressions, runtime config."""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func as sqlfunc, case as sql_case
from sqlalchemy.orm import Session

from data.models import (
    EmailCampaign,
    EmailRuntimeConfig,
    EmailSuppression,
    EmailTemplate,
    NewsletterSubscriber,
    CampaignRecipient,
)
from data.db import get_service_session
from data.services_write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
    flush_only,
)
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def _campaign_to_dict(c: EmailCampaign) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "subject": c.subject,
        "from_email": getattr(c, "from_email", None),
        "from_name": getattr(c, "from_name", None),
        "target_audience": getattr(c, "target_audience", None),
        "status": c.status,
        "scheduled_at": c.send_at.isoformat() if getattr(c, "send_at", None) else None,
        "sent_at": getattr(c, "sent_at", None).isoformat() if getattr(c, "sent_at", None) else None,
        "sent_count": getattr(c, "sent_count", 0),
        "open_count": getattr(c, "open_count", 0),
        "click_count": getattr(c, "click_count", 0),
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "created_by": getattr(c, "created_by", None),
    }


def _campaign_summary_dict(c: EmailCampaign, recipient_count: int, total_opened: int, total_clicked: int) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "subject": c.subject,
        "status": c.status,
        "recipient_count": recipient_count,
        "sent_count": recipient_count,
        "opened_count": total_opened,
        "clicked_count": total_clicked,
        "send_at": c.send_at.isoformat() if c.send_at else None,
        "sent_at": c.send_at.isoformat() if c.send_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


class EmailManagementService:
    """Service for email management DB operations."""

    def __init__(self, db: Session = None):
        self.db = db or get_service_session()

    def list_templates(self, skip: int = 0, limit: int = 20) -> List[dict]:
        templates = (
            self.db.query(EmailTemplate)
            .order_by(desc(EmailTemplate.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_serialize_template(t) for t in templates]

    def list_campaigns(self, skip: int = 0, limit: int = 20) -> List[dict]:
        campaigns = (
            self.db.query(EmailCampaign)
            .order_by(desc(EmailCampaign.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "status": c.status,
                "sent_count": c.sent_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns
        ]

    def list_suppressions(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 20
    ) -> List[dict]:
        q = self.db.query(EmailSuppression)
        if status:
            q = q.filter(EmailSuppression.status == status)
        suppressions = q.offset(skip).limit(limit).all()
        return [
            {
                "id": s.id,
                "email": s.email,
                "reason": s.reason,
                "source": s.source,
                "provider": s.provider,
                "status": s.status,
                "notes": s.notes,
                "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
                "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suppressions
        ]

    def update_suppression(
        self, suppression_id: int, body: Dict[str, Any]
    ) -> dict:
        s = self.db.query(EmailSuppression).filter(EmailSuppression.id == suppression_id).first()
        if not s:
            raise ValueError("Suppression not found")
        if "status" in body:
            s.status = body["status"]
            if body["status"] == "active" and not s.suppressed_at:
                s.suppressed_at = _utcnow()
            s.last_event_at = _utcnow()
        if "reason" in body:
            s.reason = body["reason"]
        if "notes" in body:
            s.notes = body["notes"]
        commit_and_refresh(self.db, s)
        return {
            "id": s.id,
            "email": s.email,
            "reason": s.reason,
            "source": s.source,
            "provider": s.provider,
            "status": s.status,
            "notes": s.notes,
            "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
            "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
        }

    def create_campaign(
        self, payload: Dict[str, Any], user_id: Optional[int] = None
    ) -> dict:
        campaign = EmailCampaign(
            name=payload.get("name", "Untitled Campaign"),
            subject=payload.get("subject", ""),
            status=payload.get("status", "draft"),
            target_audience=payload.get("target_audience"),
            country_code=payload.get("country_code"),
            created_by=user_id,
        )
        add_and_flush(self.db, campaign)
        commit_and_refresh(self.db, campaign)
        return {
            "id": campaign.id,
            "name": campaign.name,
            "subject": campaign.subject,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        }

    def create_campaign(
        self, payload: Dict[str, Any], country_code: str, user_id: Optional[int] = None
    ) -> dict:
        """Create a campaign scoped to a country (RLS-aware)."""
        allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
        data = {k: v for k, v in payload.items() if k in allowed and v is not None}
        data["country_code"] = country_code.upper()
        campaign = EmailCampaign(**data)
        add_and_flush(self.db, campaign)
        commit_and_refresh(self.db, campaign)
        return {
            "id": campaign.id,
            "name": campaign.name,
            "subject": campaign.subject,
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        }

    def create_template(
        self, payload: Dict[str, Any], user_id: Optional[int] = None
    ) -> dict:
        template = EmailTemplate(
            name=payload.get("name", ""),
            subject=payload.get("subject", ""),
            content=payload.get("content"),
            template_type=payload.get("template_type", "marketing"),
            created_by=user_id,
        )
        add_and_flush(self.db, template)
        commit_and_refresh(self.db, template)
        return _serialize_template(template)

    def update_template(self, template_id: int, payload: Dict[str, Any]) -> dict:
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            raise ValueError("Template not found")
        if "name" in payload:
            template.name = payload["name"]
        if "subject" in payload:
            template.subject = payload["subject"]
        if "content" in payload:
            template.content = payload["content"]
        if "template_type" in payload:
            template.template_type = payload["template_type"]
        commit_and_refresh(self.db, template)
        return _serialize_template(template)

    def delete_template(self, template_id: int) -> dict:
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        if not template:
            raise ValueError("Template not found")
        delete_only(self.db, template)
        commit_only(self.db)
        return {"message": "Template deleted", "id": template_id}

    def delete_campaign(self, campaign: EmailCampaign) -> None:
        """Delete an email campaign (entity already loaded by caller)."""
        delete_only(self.db, campaign)
        commit_only(self.db)

    def get_email_runtime_config(self) -> dict:
        cfg = self.db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
        if not cfg:
            cfg = EmailRuntimeConfig(provider="environment", smtp_port=587)
            add_and_flush(self.db, cfg)
            commit_and_refresh(self.db, cfg)
        return _email_runtime_to_dict(cfg)

    def update_email_runtime_config(self, payload: Dict[str, Any]) -> dict:
        cfg = self.db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
        if not cfg:
            cfg = EmailRuntimeConfig()
            add_and_flush(self.db, cfg)
        simple_fields = [
            "provider", "smtp_host", "smtp_port", "smtp_username",
            "smtp_use_tls", "smtp_use_ssl", "smtp_timeout_seconds",
            "email_from_default", "email_from_promotional", "email_from_transactional",
            "email_from_notification", "email_from_alert", "email_from_verification",
            "email_from_login_verification", "email_from_password_reset",
        ]
        for field in simple_fields:
            if field in payload:
                setattr(cfg, field, payload[field])
        if payload.get("resend_api_key"):
            cfg.resend_api_key = payload["resend_api_key"]
        if payload.get("resend_webhook_secret"):
            cfg.resend_webhook_secret = payload["resend_webhook_secret"]
        if payload.get("smtp_password"):
            cfg.smtp_password = payload["smtp_password"]
        commit_and_refresh(self.db, cfg)
        return _email_runtime_to_dict(cfg)

    # ── Campaign read helpers (admin) ────────────────────────────────────

    def list_all_campaigns(self, limit: int = 200) -> List[dict]:
        """List all email campaigns across all countries (consolidated admin view)."""
        campaigns = (
            self.db.query(EmailCampaign)
            .order_by(desc(EmailCampaign.created_at))
            .limit(limit)
            .all()
        )
        return [_campaign_to_dict(c) for c in campaigns]

    def get_campaigns_by_country_query(self, country_code: str):
        """Return a base query for campaigns filtered by country (for cursor pagination in router)."""
        return (
            self.db.query(EmailCampaign)
            .filter(EmailCampaign.country_code == country_code.upper())
            .order_by(desc(EmailCampaign.created_at))
        )

    def find_campaign_for_deletion(self, campaign_id: int, country_code: str) -> EmailCampaign:
        """Look up a campaign for deletion within a specific country scope."""
        campaign = (
            self.db.query(EmailCampaign)
            .filter(
                EmailCampaign.id == campaign_id,
                EmailCampaign.country_code == country_code.upper(),
            )
            .first()
        )
        if not campaign:
            raise ValueError("Campaign not found")
        return campaign

    # ── Metrics ────────────────────────────────────────────────────────────

    def get_email_metrics(self) -> dict:
        """Consolidated email metrics across all countries (admin_email.py /metrics)."""
        total_subscribers = (
            self.db.query(sqlfunc.count(NewsletterSubscriber.id))
            .filter(NewsletterSubscriber.is_active == True)
            .scalar() or 0
        )
        campaign_stats = self.db.query(
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

    def get_email_marketing_stats(self) -> dict:
        """Full marketing stats including open/click rates (admin.py /email/stats)."""
        total_subscribers = (
            self.db.query(sqlfunc.count(NewsletterSubscriber.id))
            .filter(NewsletterSubscriber.is_active == True)
            .scalar() or 0
        )

        campaign_stats = self.db.query(
            sqlfunc.count(EmailCampaign.id).label("total"),
            sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
        ).first()

        total_sent = (
            self.db.query(sqlfunc.count(CampaignRecipient.id))
            .filter(CampaignRecipient.sent_at.isnot(None))
            .scalar() or 0
        )
        total_opened = (
            self.db.query(sqlfunc.count(CampaignRecipient.id))
            .filter(CampaignRecipient.opened_at.isnot(None))
            .scalar() or 0
        )
        total_clicked = (
            self.db.query(sqlfunc.count(CampaignRecipient.id))
            .filter(CampaignRecipient.clicked_at.isnot(None))
            .scalar() or 0
        )

        open_rate = round((total_opened / total_sent * 100), 1) if total_sent else 0
        click_rate = round((total_clicked / total_opened * 100), 1) if total_opened else 0

        recent_campaigns = (
            self.db.query(EmailCampaign)
            .order_by(desc(EmailCampaign.created_at))
            .limit(10)
            .all()
        )

        def _ser_campaign(c: EmailCampaign):
            recipient_count = (
                self.db.query(sqlfunc.count(CampaignRecipient.id))
                .filter(CampaignRecipient.campaign_id == c.id)
                .scalar() or 0
            )
            return _campaign_summary_dict(c, recipient_count, total_opened, total_clicked)

        return {
            "total_subscribers": total_subscribers,
            "active_campaigns": int(campaign_stats.active or 0),
            "total_campaigns": int(campaign_stats.total or 0),
            "total_sent": total_sent,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "recent_campaigns": [_ser_campaign(c) for c in recent_campaigns],
        }


def _serialize_template(t: EmailTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "subject": t.subject,
        "content": t.content,
        "template_type": t.template_type,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _email_runtime_to_dict(cfg: EmailRuntimeConfig) -> dict:
    resend_key = bool(cfg.resend_api_key)
    resend_secret = bool(cfg.resend_webhook_secret)
    return {
        "id": cfg.id,
        "provider": cfg.provider,
        "active_provider": cfg.provider,
        "source": "db",
        "available": True,
        "live": cfg.provider not in ("disabled", None),
        "preview_only": cfg.provider == "environment",
        "supports_webhooks": True,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port or 587,
        "smtp_username": cfg.smtp_username,
        "smtp_use_tls": cfg.smtp_use_tls,
        "smtp_use_ssl": cfg.smtp_use_ssl,
        "smtp_timeout_seconds": cfg.smtp_timeout_seconds or 15,
        "email_from_default": cfg.email_from_default,
        "email_from_promotional": cfg.email_from_promotional,
        "email_from_transactional": cfg.email_from_transactional,
        "email_from_notification": cfg.email_from_notification,
        "email_from_alert": cfg.email_from_alert,
        "email_from_verification": cfg.email_from_verification,
        "email_from_login_verification": cfg.email_from_login_verification,
        "email_from_password_reset": cfg.email_from_password_reset,
        "resend_api_key_configured": resend_key,
        "resend_webhook_secret_configured": resend_secret,
        "smtp_password_configured": bool(cfg.smtp_password),
    }


def get_email_management_service(db: Session = None) -> EmailManagementService:
    return EmailManagementService(db or get_service_session())
