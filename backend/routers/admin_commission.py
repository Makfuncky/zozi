"""Admin commission router."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from db.database import get_db
from models import CommissionCategoryRate, CommissionBadgeTier, CommissionGlobalConfig, User
from db.schemas import CommissionCategoryRateCreate, CommissionCategoryRateOut, CommissionBadgeTierCreate, CommissionBadgeTierOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter()


def _build_category_rate(payload: CommissionCategoryRateCreate, country_code: str) -> CommissionCategoryRate:
    data = payload.model_dump() if payload else {}
    return CommissionCategoryRate(
        category_id=data.get("category_id"),
        category_slug=data.get("category_slug"),
        category_display_name=data.get("category_display_name"),
        rate_percent=data.get("rate", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


def _build_badge_tier(payload: CommissionBadgeTierCreate, country_code: str) -> CommissionBadgeTier:
    data = payload.model_dump() if payload else {}
    return CommissionBadgeTier(
        badge_level=data.get("badge_level"),
        commission_rate=data.get("commission_rate", 0),
        min_fulfilled_orders=data.get("min_fulfilled_orders", 0),
        is_active=data.get("is_active", True),
        country_code=country_code.upper(),
    )


@router.get("/{country_code}/rates")
def list_rates(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.country_code == country_code.upper())
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/{country_code}/rates", response_model=CommissionCategoryRateOut, status_code=201)
def create_rate(country_code: str = Path(..., description="ISO country code"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        r = _build_category_rate(payload, country_code)
        db.add(r); db.commit(); db.refresh(r)
        return r
    finally:
        clear_rls_context()


@router.put("/{country_code}/rates/{rate_id}", response_model=CommissionCategoryRateOut)
def update_rate(country_code: str = Path(..., description="ISO country code"), rate_id: int = Path(..., description="Rate id"), payload: CommissionCategoryRateCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    r = db.query(CommissionCategoryRate).filter(CommissionCategoryRate.id == rate_id, CommissionCategoryRate.country_code == country_code.upper()).first()
    if not r:
        raise HTTPException(status_code=404, detail="Category rate not found")
    data = payload.model_dump() if payload else {}
    r.category_id = data.get("category_id", r.category_id)
    r.category_slug = data.get("category_slug", r.category_slug)
    r.category_display_name = data.get("category_display_name", r.category_display_name)
    if "rate" in data:
        r.rate_percent = data["rate"]
    r.is_active = data.get("is_active", r.is_active)
    db.commit(); db.refresh(r)
    return r


@router.get("/{country_code}/badge-tiers")
def list_badge_tiers(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.country_code == country_code.upper())
        total = q.count()
        rows = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()


@router.post("/{country_code}/badge-tiers", response_model=CommissionBadgeTierOut, status_code=201)
def create_badge_tier(country_code: str = Path(..., description="ISO country code"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        t = _build_badge_tier(payload, country_code)
        db.add(t); db.commit(); db.refresh(t)
        return t
    finally:
        clear_rls_context()


@router.put("/{country_code}/badge-tiers/{tier_id}", response_model=CommissionBadgeTierOut)
def update_badge_tier(country_code: str = Path(..., description="ISO country code"), tier_id: int = Path(..., description="Badge tier id"), payload: CommissionBadgeTierCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    t = db.query(CommissionBadgeTier).filter(CommissionBadgeTier.id == tier_id, CommissionBadgeTier.country_code == country_code.upper()).first()
    if not t:
        raise HTTPException(status_code=404, detail="Badge tier not found")
    data = payload.model_dump() if payload else {}
    t.badge_level = data.get("badge_level", t.badge_level)
    t.commission_rate = data.get("commission_rate", t.commission_rate)
    t.min_fulfilled_orders = data.get("min_fulfilled_orders", t.min_fulfilled_orders)
    t.is_active = data.get("is_active", t.is_active)
    db.commit(); db.refresh(t)
    return t

