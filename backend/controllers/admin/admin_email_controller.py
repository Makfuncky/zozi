"""Admin email campaign controller.

Thin delegation layer between ``routers/admin_email.py`` and
``services/comms/email_write_service.py``.

Country resolution, RLS scoping and existence lookups (all reads) stay here;
every DB mutation is delegated to the write service so the router and this
controller remain free of Layer-1 write leakage (W1 layer contract).
``HTTPException`` raised by either layer propagates untouched.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import EmailCampaign
from services.comms.email_write_service import (
    create_email_campaign,
    delete_email_campaign,
)
from services.db_read import first
from utils.country_access import get_country_or_404
from utils.rls_interceptor import clear_rls_context, set_rls_context
import structlog
logger = structlog.get_logger(__name__)

# Whitelist of campaign fields accepted from the create payload.
_CAMPAIGN_CREATE_FIELDS = {"name", "subject", "status", "send_at", "created_by", "country_code"}


def create_campaign(country_code: str, payload, db: Session) -> EmailCampaign:
    """Create an email campaign scoped to ``country_code``."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        data = {
            k: v
            for k, v in payload.model_dump().items()
            if k in _CAMPAIGN_CREATE_FIELDS and v is not None
        }
        data["country_code"] = code
        return create_email_campaign(db, **data)
    finally:
        clear_rls_context()


def delete_campaign(country_code: str, campaign_id: int, db: Session) -> dict:
    """Delete a country-scoped email campaign."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        campaign = first(
            db,
            EmailCampaign,
            [EmailCampaign.id == campaign_id, EmailCampaign.country_code == code],
        )
        if not campaign:
            raise HTTPException(404)
        delete_email_campaign(db, campaign)
        return {"message": "Deleted"}
    finally:
        clear_rls_context()
