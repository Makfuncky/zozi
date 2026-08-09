"""Controller for the country-scoped admin commission management router.

Thin orchestration layer between `routers.admin_commission_governance` and
`services.finance.commission_admin_write_service`. The router stays free of
`db.add`/`db.commit` (W1); 404 handling lives here so the router remains a
thin boundary.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.finance.commission_admin_write_service import (
    create_commission_badge_tier,
    create_commission_category_rate,
    update_commission_badge_tier_by_id,
    update_commission_category_rate_by_id,
)
import structlog
logger = structlog.get_logger(__name__)


def create_category_rate(country_code: str, payload: Optional[dict], db: Session):
    return create_commission_category_rate(payload or {}, country_code, db)


def update_category_rate(rate_id: int, country_code: str, payload: Optional[dict], db: Session):
    rate = update_commission_category_rate_by_id(rate_id, country_code, payload or {}, db)
    if rate is None:
        raise HTTPException(status_code=404, detail="Category rate not found")
    return rate


def create_badge_tier(country_code: str, payload: Optional[dict], db: Session):
    return create_commission_badge_tier(payload or {}, country_code, db)


def update_badge_tier(tier_id: int, country_code: str, payload: Optional[dict], db: Session):
    tier = update_commission_badge_tier_by_id(tier_id, country_code, payload or {}, db)
    if tier is None:
        raise HTTPException(status_code=404, detail="Badge tier not found")
    return tier
