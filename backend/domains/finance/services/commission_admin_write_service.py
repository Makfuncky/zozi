"""Country-scoped commission admin write service.

Owns DB writes for the admin commission management router
(`backend/routers/admin_commission.py`). Kept independent of the legacy
`services.finance.commission_write_service` re-export shim to avoid the
controller<->service circular import in that module.

Functions are db-param (the session is passed in by the calling controller),
per the backend grid-line contract: routers/controllers must not issue
`db.add`/`db.commit` directly (W1).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models import CommissionBadgeTier, CommissionCategoryRate
from services.finance.commission_write_service import apply_changes
import structlog
logger = structlog.get_logger(__name__)


def create_commission_category_rate(payload: dict, country_code: str, db: Session) -> CommissionCategoryRate:
    data = payload or {}
    rate = CommissionCategoryRate(
        category_id=data.get("category_id"),
        category_slug=data.get("category_slug"),
        category_display_name=data.get("category_display_name"),
        rate_percent=data.get("rate", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_commission_category_rate_by_id(
    rate_id: int, country_code: str, payload: dict, db: Session
) -> Optional[CommissionCategoryRate]:
    data = payload or {}
    rate = (
        db.query(CommissionCategoryRate)
        .filter(
            CommissionCategoryRate.id == rate_id,
            CommissionCategoryRate.country_code == country_code.upper(),
        )
        .first()
    )
    if rate is None:
        return None
    changes = dict(data)
    if "rate" in changes:
        changes["rate_percent"] = changes.pop("rate")
    _apply_changes(rate, changes)
    db.commit()
    db.refresh(rate)
    return rate


def create_commission_badge_tier(payload: dict, country_code: str, db: Session) -> CommissionBadgeTier:
    data = payload or {}
    tier = CommissionBadgeTier(
        badge_level=data.get("badge_level"),
        commission_rate=data.get("commission_rate", 0),
        min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def update_commission_badge_tier_by_id(
    tier_id: int, country_code: str, payload: dict, db: Session
) -> Optional[CommissionBadgeTier]:
    data = payload or {}
    tier = (
        db.query(CommissionBadgeTier)
        .filter(
            CommissionBadgeTier.id == tier_id,
            CommissionBadgeTier.country_code == country_code.upper(),
        )
        .first()
    )
    if tier is None:
        return None
    _apply_changes(tier, data)
    db.commit()
    db.refresh(tier)
    return tier
