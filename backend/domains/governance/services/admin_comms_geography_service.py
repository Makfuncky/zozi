"""Auto-migrated service logic from routers/admin_comms_geography.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from models import User

from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

from services.comms.campaign_geography_service import (
    create_campaign,
    delete_campaign,
    email_metrics,
    list_all_campaigns,
    list_campaigns,
)

def list_all_campaigns_route(_: User, db: Session):
    """List all email campaigns across all countries (consolidated view)."""
    return list_all_campaigns(db)

def admin_email_metrics(_: User, db: Session):
    """Consolidated email metrics across all countries."""
    return email_metrics(db)

def list_campaigns_route(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_campaigns(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_campaign_route(country_code: str, payload: EmailCampaignCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_campaign(db, payload, country_code)
    finally:
        clear_rls_context()

def delete_campaign_route(country_code: str, campaign_id: int, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return delete_campaign(db, campaign_id, country_code)
    finally:
        clear_rls_context()


