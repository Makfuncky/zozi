"""
Commission Router — admin endpoints for managing the full commission engine.
All endpoints require admin role.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from db.schemas import ListPage
from utils.dependencies import require_admin
from controllers import commission_controller

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CommissionRateBody(BaseModel):
    rate: float = Field(..., ge=0.0, le=1.0, description="Commission rate as decimal, e.g. 0.12 for 12%")
    note: Optional[str] = Field(None, max_length=500)


class GlobalConfigBody(BaseModel):
    default_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    low_value_threshold: Optional[float] = Field(None, ge=0.0)
    fixed_cap_amount: Optional[float] = Field(None, ge=0.0)
    fixed_cap_enabled: Optional[bool] = None
    margin_protection_enabled: Optional[bool] = None
    margin_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class CategoryRateBody(BaseModel):
    rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    category_display_name: Optional[str] = Field(None, max_length=150)


class BadgeTierBody(BaseModel):
    commission_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    setup_fee: Optional[float] = Field(None, ge=0.0)
    recurring_fee: Optional[float] = Field(None, ge=0.0)
    recurring_interval: Optional[str] = Field(None, max_length=20)
    benefits_json: Optional[str] = None
    min_fulfilled_orders: Optional[int] = None
    min_monthly_revenue: Optional[float] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class LedgerAdjustmentBody(BaseModel):
    new_amount: float = Field(..., ge=0.0)
    reason: str = Field(..., min_length=5, max_length=1000)


class PreviewBody(BaseModel):
    supplier_id: int
    order_value: float = Field(..., gt=0.0)
    category_slug: Optional[str] = None


# ── Global config ─────────────────────────────────────────────────────────────

@router.get("/global", summary="Get global commission config")
def get_global_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.get_global_config(db)


@router.put("/global", summary="Update global commission config")
def update_global_config(
    body: GlobalConfigBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_global_config(payload, current_user, db)


# ── Category rates ────────────────────────────────────────────────────────────

@router.get("/categories", response_model=ListPage[dict], summary="List all category commission rates")
def list_category_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.put("/categories/{category_slug}", summary="Update a category commission rate")
def update_category_rate(
    category_slug: str,
    body: CategoryRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_category_rate(category_slug, payload, current_user, db)


# ── Badge tiers ───────────────────────────────────────────────────────────────

@router.get("/badge-tiers", response_model=ListPage[dict], summary="List all badge tiers")
def list_badge_tiers(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)


@router.put("/badge-tiers/{badge_level}", summary="Update a badge tier")
def update_badge_tier(
    badge_level: str,
    body: BadgeTierBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_badge_tier(badge_level, payload, current_user, db)


# ── Commission ledger ─────────────────────────────────────────────────────────

@router.get("/ledger", summary="List commission ledger entries")
def list_ledger_entries(
    supplier_id: Optional[int] = None,
    order_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_ledger_entries(db, supplier_id, order_id, skip, limit)


@router.put("/ledger/{ledger_id}/adjust", summary="Adjust a ledger entry (dispute resolution)")
def adjust_ledger_entry(
    ledger_id: int,
    body: LedgerAdjustmentBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.create_ledger_adjustment(
        ledger_id=ledger_id,
        new_amount=body.new_amount,
        reason=body.reason,
        acting_user=current_user,
        db=db,
    )


# ── Preview calculator (no DB writes) ─────────────────────────────────────────

@router.post("/preview", summary="Preview commission calculation without persisting")
def preview_commission(
    body: PreviewBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.preview_commission(
        supplier_id=body.supplier_id,
        order_value=body.order_value,
        category_slug=body.category_slug,
        db=db,
    )


# ── All suppliers overview ────────────────────────────────────────────────────

@router.get("/suppliers", response_model=ListPage[dict], summary="List all suppliers with current commission rates")
def list_supplier_commissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)


# ── Supplier-level commission ─────────────────────────────────────────────────

@router.get("/suppliers/{supplier_id}", summary="Get supplier commission rate + history")
def get_supplier_commission(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.get_supplier_commission(supplier_id, db)


@router.post("/suppliers/{supplier_id}", status_code=201, summary="Set supplier commission override")
def set_supplier_commission(
    supplier_id: int,
    body: CommissionRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.set_supplier_commission(
        supplier_id=supplier_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


@router.delete("/suppliers/{supplier_id}", summary="Remove supplier commission override")
def delete_supplier_commission_override(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.delete_supplier_commission_override(
        supplier_id=supplier_id,
        acting_user=current_user,
        db=db,
    )


# ── Product-level commission override ────────────────────────────────────────

@router.get("/products/{product_id}", summary="Get product commission override")
def get_product_commission_override(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = commission_controller.get_product_commission_override(product_id, db)
    if result is None:
        return {"override": None, "message": "No override — using category/badge/default rate"}
    return result


@router.get("/product-overrides", summary="List product commission overrides")
def list_product_commission_overrides(
    search: Optional[str] = None,
    supplier_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.list_product_commission_overrides(
        db,
        search=search,
        supplier_id=supplier_id,
        limit=limit,
    )


@router.post("/products/{product_id}", status_code=201, summary="Set product commission override")
def set_product_commission_override(
    product_id: int,
    body: CommissionRateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.set_product_commission_override(
        product_id=product_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )


@router.delete("/products/{product_id}", summary="Remove product commission override")
def delete_product_commission_override(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return commission_controller.delete_product_commission_override(
        product_id=product_id,
        acting_user=current_user,
        db=db,
    )


# ── Effective rate calculator (backwards-compatible) ─────────────────────────

@router.get("/effective-rate", summary="Get effective commission rate for a supplier (engine)")
def get_effective_rate(
    supplier_id: int,
    product_id: Optional[int] = None,
    category_slug: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    from services.commission_engine import get_effective_rate as _engine_rate
    result = _engine_rate(supplier_id=supplier_id, product_id=product_id,
                          category_slug=category_slug, db=db)
    return {
        "rate": float(result.applied_rate),
        "percentage": f"{float(result.applied_rate) * 100:.2f}%",
        "calculation_method": result.calculation_method,
        "supplier_rate": float(result.supplier_rate),
        "supplier_rate_source": result.supplier_rate_source,
        "base_rate": float(result.base_rate),
        "base_rate_source": result.base_rate_source,
        "product_override_rate": float(result.product_override_rate) if result.product_override_rate else None,
        "badge_level": result.badge_level,
        "category_slug": result.category_slug,
        "override_flag": result.override_flag,
    }

