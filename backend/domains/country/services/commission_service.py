"""Auto-migrated service logic from routers/commission.py."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from modules.finance.routers import commission_controller

from modules.admin.routers.auth import require_admin
from infrastructure.database.database import get_db

from infrastructure.database.schemas import ListPage

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

def get_global_config(db: Session, current_user: dict):
    return commission_controller.get_global_config(db)

def update_global_config(body: GlobalConfigBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_global_config(payload, current_user, db)

def list_category_rates(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return commission_controller.list_category_rates(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def update_category_rate(category_slug: str, body: CategoryRateBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_category_rate(category_slug, payload, current_user, db)

def list_badge_tiers(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return commission_controller.list_badge_tiers(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def update_badge_tier(badge_level: str, body: BadgeTierBody, db: Session, current_user: dict):
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    return commission_controller.update_badge_tier(badge_level, payload, current_user, db)

def list_ledger_entries(supplier_id: Optional[int], order_id: Optional[int], skip: int, limit: int, db: Session, current_user: dict):
    return commission_controller.list_ledger_entries(db, supplier_id, order_id, skip, limit)

def adjust_ledger_entry(ledger_id: int, body: LedgerAdjustmentBody, db: Session, current_user: dict):
    return commission_controller.create_ledger_adjustment(
        ledger_id=ledger_id,
        new_amount=body.new_amount,
        reason=body.reason,
        acting_user=current_user,
        db=db,
    )

def preview_commission(body: PreviewBody, db: Session, current_user: dict):
    return commission_controller.preview_commission(
        supplier_id=body.supplier_id,
        order_value=body.order_value,
        category_slug=body.category_slug,
        db=db,
    )

def list_supplier_commissions(page: int, page_size: int, search: Optional[str], db: Session, current_user: dict):
    return commission_controller.list_all_supplier_commissions(db, limit=page_size, offset=(page - 1) * page_size, search=search)

def get_supplier_commission(supplier_id: int, db: Session, current_user: dict):
    return commission_controller.get_supplier_commission(supplier_id, db)

def set_supplier_commission(supplier_id: int, body: CommissionRateBody, db: Session, current_user: dict):
    return commission_controller.set_supplier_commission(
        supplier_id=supplier_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )

def delete_supplier_commission_override(supplier_id: int, db: Session, current_user: dict):
    return commission_controller.delete_supplier_commission_override(
        supplier_id=supplier_id,
        acting_user=current_user,
        db=db,
    )

def get_product_commission_override(product_id: int, db: Session, current_user: dict):
    result = commission_controller.get_product_commission_override(product_id, db)
    if result is None:
        return {"override": None, "message": "No override — using category/badge/default rate"}
    return result

def list_product_commission_overrides(search: Optional[str], supplier_id: Optional[int], limit: int, db: Session, current_user: dict):
    return commission_controller.list_product_commission_overrides(
        db,
        search=search,
        supplier_id=supplier_id,
        limit=limit,
    )

def set_product_commission_override(product_id: int, body: CommissionRateBody, db: Session, current_user: dict):
    return commission_controller.set_product_commission_override(
        product_id=product_id,
        rate=body.rate,
        note=body.note,
        acting_user=current_user,
        db=db,
    )

def delete_product_commission_override(product_id: int, db: Session, current_user: dict):
    return commission_controller.delete_product_commission_override(
        product_id=product_id,
        acting_user=current_user,
        db=db,
    )

def get_effective_rate(supplier_id: int, product_id: Optional[int], category_slug: Optional[str], db: Session, current_user: dict):
    from domains.finance.services.commission.commission_engine import get_effective_rate as _engine_rate
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

