"""Auto-migrated service logic from routers/admin_finance_geography.py."""
from __future__ import annotations

from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from _legacy.models import User

from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut

from infrastructure.utils.dependencies import require_admin

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

from services.finance.commission_geography_service import (
    create_badge_tier,
    create_category_rate,
    list_badge_tiers,
    list_category_rates,
    update_badge_tier,
    update_category_rate,
)

def list_rates(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_rate(country_code: str, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()

def update_rate(country_code: str, rate_id: int, payload: CommissionCategoryRateCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)

def list_badge_tiers_route(country_code: str, _: User, db: Session, page: int, page_size: int):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()

def create_badge_tier_route(country_code: str, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()

def update_badge_tier_route(country_code: str, tier_id: int, payload: CommissionBadgeTierCreate, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)


