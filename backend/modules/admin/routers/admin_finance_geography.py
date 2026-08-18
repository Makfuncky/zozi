"""Admin commission router."""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.accounts.models.user import User
from infrastructure.database.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from domains.finance.services.commission_geography_service import create_badge_tier
from domains.finance.services.commission_geography_service import create_category_rate
from domains.finance.services.commission_geography_service import list_badge_tiers
from domains.finance.services.commission_geography_service import list_category_rates
from domains.finance.services.commission_geography_service import update_badge_tier
from domains.finance.services.commission_geography_service import update_category_rate

router = APIRouter(prefix="/api/v1/admin")


@router.get("/{country_code}/rates")
def list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_category_rates(db, country_code, page, page_size)
    finally:
        clear_rls_context()


@router.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)
def create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_category_rate(db, payload, country_code)
    finally:
        clear_rls_context()


@router.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)
def update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return update_category_rate(db, rate_id, country_code, payload)


@router.get("/{country_code}/badge-tiers")
def list_badge_tiers_route(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return list_badge_tiers(db, country_code, page, page_size)
    finally:
        clear_rls_context()


@router.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)
def create_badge_tier_route(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return create_badge_tier(db, payload, country_code)
    finally:
        clear_rls_context()


@router.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)
def update_badge_tier_route(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    return update_badge_tier(db, tier_id, country_code, payload)
