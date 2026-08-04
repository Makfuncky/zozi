"""Admin commission router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage
from data.models import CommissionCategoryRate, CommissionBadgeTier, User
from data.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut
from utils.dependencies import require_admin
from utils.pagination import cursor_paginate_desc
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from services.commission_write_service import (
    create_commission_category_rate as create_category_rate_db,
    create_commission_badge_tier as create_badge_tier_db,
    update_commission_category_rate as update_category_rate_db,
    update_commission_badge_tier as update_badge_tier_db,
    list_commission_rates as list_rates_db,
    get_commission_rate_by_id as get_rate_db,
    list_commission_tiers as list_tiers_db,
    get_commission_tier_by_id as get_tier_db,
)

router = APIRouter()


@router.get("/{country_code}/rates", response_model=CursorPage)
def list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), cursor: str | None = Query(None, description="Cursor for next page"), limit: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = list_rates_db(db, country_code)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)
def create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        data = payload.model_dump() if payload else {}
        return create_category_rate_db(
            db,
            category_id=data.get("category_id"),
            category_slug=data.get("category_slug"),
            category_display_name=data.get("category_display_name"),
            rate_percent=data.get("rate", 0),
            is_active=data.get("is_active", True),
            country_code=country_code.upper(),
        )
    finally:
        clear_rls_context()


@router.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)
def update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    r = get_rate_db(db, rate_id, country_code)
    if not r:
        raise HTTPException(status_code=404, detail="Category rate not found")
    data = payload.model_dump() if payload else {}
    updates = {
        "category_id": data.get("category_id", r.category_id),
        "category_slug": data.get("category_slug", r.category_slug),
        "category_display_name": data.get("category_display_name", r.category_display_name),
        "rate_percent": data.get("rate", r.rate_percent),
        "is_active": data.get("is_active", r.is_active),
    }
    return update_category_rate_db(db, r, updates)


@router.get("/{country_code}/badge-tiers", response_model=CursorPage)
def list_badge_tiers(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), cursor: str | None = Query(None, description="Cursor for next page"), limit: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = list_tiers_db(db, country_code)
        return cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    finally:
        clear_rls_context()


@router.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)
def create_badge_tier(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        data = payload.model_dump() if payload else {}
        return create_badge_tier_db(
            db,
            badge_level=data.get("badge_level"),
            commission_rate=data.get("commission_rate", 0),
            min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
            is_active=data.get("is_active", True),
            country_code=country_code.upper(),
        )
    finally:
        clear_rls_context()


@router.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)
def update_badge_tier(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    t = get_tier_db(db, tier_id, country_code)
    if not t:
        raise HTTPException(status_code=404, detail="Badge tier not found")
    data = payload.model_dump() if payload else {}
    updates = {
        "badge_level": data.get("badge_level", t.badge_level),
        "commission_rate": data.get("commission_rate", t.commission_rate),
        "min_fulfilled_orders": data.get("min_fulfilled_orders", t.min_fulfilled_orders),
        "is_active": data.get("is_active", t.is_active),
    }
    return update_badge_tier_db(db, t, updates)