"""Country-scoped commission (category rate + badge tier) read/write operations.

Owns the DB reads/writes for ``admin_finance_geography`` so the router stays
free of ``db.query``/``db.add``/``db.commit``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import CommissionBadgeTier, CommissionCategoryRate
import structlog
logger = structlog.get_logger(__name__)


def build_category_rate(payload, country_code: str) -> CommissionCategoryRate:
    data = payload.model_dump() if payload else {}
    return CommissionCategoryRate(
        category_id=data.get("category_id"),
        category_slug=data.get("category_slug"),
        category_display_name=data.get("category_display_name"),
        rate_percent=data.get("rate", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


def build_badge_tier(payload, country_code: str) -> CommissionBadgeTier:
    data = payload.model_dump() if payload else {}
    return CommissionBadgeTier(
        badge_level=data.get("badge_level"),
        commission_rate=data.get("commission_rate", 0),
        min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


def list_category_rates(db: Session, country_code: str, page: int, page_size: int) -> dict:
    q = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.country_code == country_code.upper())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def create_category_rate(db: Session, payload, country_code: str) -> CommissionCategoryRate:
    r = build_category_rate(payload, country_code)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_category_rate(db: Session, rate_id: int, country_code: str, payload) -> CommissionCategoryRate:
    r = (
        db.query(CommissionCategoryRate)
        .filter(CommissionCategoryRate.id == rate_id, CommissionCategoryRate.country_code == country_code.upper())
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Category rate not found")
    data = payload.model_dump() if payload else {}
    r.category_id = data.get("category_id", r.category_id)
    r.category_slug = data.get("category_slug", r.category_slug)
    r.category_display_name = data.get("category_display_name", r.category_display_name)
    if "rate" in data:
        r.rate_percent = data["rate"]
    r.is_active = data.get("is_active", r.is_active)
    db.commit()
    db.refresh(r)
    return r


def list_badge_tiers(db: Session, country_code: str, page: int, page_size: int) -> dict:
    q = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.country_code == country_code.upper())
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def create_badge_tier(db: Session, payload, country_code: str) -> CommissionBadgeTier:
    t = build_badge_tier(payload, country_code)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_badge_tier(db: Session, tier_id: int, country_code: str, payload) -> CommissionBadgeTier:
    t = (
        db.query(CommissionBadgeTier)
        .filter(CommissionBadgeTier.id == tier_id, CommissionBadgeTier.country_code == country_code.upper())
        .first()
    )
    if not t:
        raise HTTPException(status_code=404, detail="Badge tier not found")
    data = payload.model_dump() if payload else {}
    t.badge_level = data.get("badge_level", t.badge_level)
    t.commission_rate = data.get("commission_rate", t.commission_rate)
    t.min_fulfilled_orders = data.get("min_fulfilled_orders", t.min_fulfilled_orders)
    t.is_active = data.get("is_active", t.is_active)
    db.commit()
    db.refresh(t)
    return t
