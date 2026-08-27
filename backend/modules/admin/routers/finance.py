"""Admin finance router — thin HTTP layer delegating to finance domain services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.finance.services.ledger.general_ledger_service import (
    create_category_rate,
    list_category_rates,
    update_category_rate,
)
from domains.finance.services.country.admin_commission_service import (
    create_badge_tier,
    list_badge_tiers,
    update_badge_tier,
)

router = APIRouter(prefix="/api/v1/admin/finance", tags=["admin", "finance"])


@router.get("/{country_code}/rates")
def list_rates(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    require_feature("finance.commission.read")
    return list_category_rates(db, country_code, page, page_size)


@router.post("/{country_code}/rates", status_code=201)
def create_rate(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("finance.commission.write")
    return create_category_rate(db, payload, country_code)


@router.put("/{country_code}/rates/{rate_id}")
def update_rate(
    country_code: str = Path(..., description="ISO country code"),
    rate_id: int = Path(..., description="Rate id"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("finance.commission.write")
    return update_category_rate(db, rate_id, country_code, payload)


@router.get("/{country_code}/badge-tiers")
def list_badge_tiers_route(
    country_code: str = Path(..., description="ISO country code"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    require_feature("finance.commission.read")
    return list_badge_tiers(country_code, page, page_size, db)


@router.post("/{country_code}/badge-tiers", status_code=201)
def create_badge_tier_route(
    country_code: str = Path(..., description="ISO country code"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("finance.commission.write")
    from infrastructure.database.schemas import CommissionBadgeTierCreate
    typed_payload = CommissionBadgeTierCreate(**payload) if isinstance(payload, dict) else payload
    return create_badge_tier(country_code, typed_payload, db)


@router.put("/{country_code}/badge-tiers/{tier_id}")
def update_badge_tier_route(
    country_code: str = Path(..., description="ISO country code"),
    tier_id: int = Path(..., description="Badge tier id"),
    payload: dict = Body(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("finance.commission.write")
    typed_payload = CommissionBadgeTierCreate(**payload) if isinstance(payload, dict) else payload
    return update_badge_tier(country_code, tier_id, typed_payload, db)
